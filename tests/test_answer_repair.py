from recharness import (
    AgentHarnessRouter,
    AssistRequest,
    ClaimIssue,
    VerificationReport,
    VerifyRequest,
    repair_or_qualify_answer,
)
from recharness.core import repair_or_qualify_answer as core_repair_or_qualify_answer
from recharness.core.answer_repair import repair_answer_from_verification


def _router() -> AgentHarnessRouter:
    return AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")


def test_repair_leaves_safe_verified_answer_unchanged():
    router = _router()
    answer = "我推荐 OfficeClear Call 32，售价799元，有主动降噪。"
    verify = router.verify(
        VerifyRequest(
            user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
            domain="headphones",
            agent_answer=answer,
        )
    )

    result = repair_answer_from_verification(answer, verify)

    assert result.status == "unchanged"
    assert result.repaired_answer == answer
    assert result.changes == []
    assert result.warnings == []


def test_repair_corrects_catalog_grounded_claim_mistakes():
    router = _router()
    answer = "我推荐 SonicLite AirBuds，售价699元，有主动降噪，续航30小时。"
    verify = router.verify(
        VerifyRequest(
            user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
            domain="headphones",
            agent_answer=answer,
        )
    )

    result = repair_answer_from_verification(answer, verify)

    assert result.status == "repaired"
    assert "有主动降噪" not in result.repaired_answer
    assert "续航30小时" not in result.repaired_answer
    assert "24" in result.repaired_answer
    assert any("noise_cancellation" in change for change in result.changes)
    assert any("battery_life" in change for change in result.changes)


def test_repair_replaces_hard_constraint_invalid_recommendation_when_safe_candidate_exists():
    router = _router()
    query = "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop."
    answer = "I recommend RainGuard Metro Pack 24L. It costs 1599 RMB."
    assist = router.assist(AssistRequest(user_query=query, domain="backpacks", top_k=2))
    verify = router.verify(
        VerifyRequest(user_query=query, domain="backpacks", agent_answer=answer)
    )

    result = repair_answer_from_verification(answer, verify, assist)

    assert result.status == "repaired"
    assert "RainGuard Metro Pack 24L" not in result.repaired_answer
    assert assist.bundle is not None
    assert assist.bundle.recommended[0].product.title in result.repaired_answer
    assert "local catalog indicates" in result.repaired_answer
    assert any("hard constraint" in change for change in result.changes)


def test_repair_corrects_hard_factual_claim_without_replacing_valid_product():
    router = _router()
    query = "想找1000元以内，适合通勤，有降噪的蓝牙耳机"
    answer = "我推荐 OfficeClear Call 32，售价1元，有主动降噪。"
    assist = router.assist(AssistRequest(user_query=query, domain="headphones", top_k=3))
    verify = router.verify(
        VerifyRequest(user_query=query, domain="headphones", agent_answer=answer)
    )

    result = repair_answer_from_verification(answer, verify, assist)

    assert result.status == "repaired"
    assert "OfficeClear Call 32" in result.repaired_answer
    assert "售价799元" in result.repaired_answer
    assert assist.bundle is not None
    assert assist.bundle.recommended[1].product.title not in result.repaired_answer


def test_repair_replaces_unresolved_product_when_safe_candidate_exists():
    router = _router()
    query = "Need headphones under 1000 RMB"
    answer = "I recommend NotReal Product. It costs 1 RMB."
    assist = router.assist(AssistRequest(user_query=query, domain="headphones", top_k=1))
    verify = router.verify(
        VerifyRequest(user_query=query, domain="headphones", agent_answer=answer)
    )

    result = repair_answer_from_verification(answer, verify, assist)

    assert result.status == "repaired"
    assert "NotReal Product" not in result.repaired_answer
    assert assist.bundle is not None
    assert assist.bundle.recommended[0].product.title in result.repaired_answer


def test_repair_qualifies_when_no_safe_repair_is_available():
    router = _router()
    answer = "I recommend NotReal Product. It costs 1 RMB."
    verify = router.verify(
        VerifyRequest(
            user_query="Need headphones under 1000 RMB",
            domain="headphones",
            agent_answer=answer,
        )
    )

    result = repair_answer_from_verification(answer, verify)

    assert result.status == "qualified"
    assert result.repaired_answer.startswith(answer)
    assert "local catalog" in result.repaired_answer
    assert result.warnings


def test_chinese_repair_note_does_not_use_english_local_catalog_phrase():
    router = _router()
    answer = "我推荐 CallMate USB Office，售价399元，有主动降噪。"
    verify = router.verify(
        VerifyRequest(
            user_query="Need office headphones for calls with microphone noise reduction",
            domain="headphones",
            agent_answer=answer,
        )
    )

    result = repair_answer_from_verification(answer, verify)

    assert result.status == "repaired"
    assert "Local catalog indicates" not in result.repaired_answer
    assert "本地目录标注" in result.repaired_answer


def test_english_repair_note_uses_english_local_catalog_phrase():
    router = _router()
    answer = "I recommend CallMate USB Office with active noise cancellation."
    verify = router.verify(
        VerifyRequest(
            user_query="Need office headphones for calls with microphone noise reduction",
            domain="headphones",
            agent_answer=answer,
        )
    )

    result = repair_answer_from_verification(answer, verify)

    assert result.status == "repaired"
    assert "Local catalog indicates" in result.repaired_answer


def test_repair_or_qualify_answer_is_publicly_exported():
    assert repair_or_qualify_answer is core_repair_or_qualify_answer


def test_price_repair_does_not_replace_unrelated_number_without_price_context():
    report = VerificationReport(
        status="fail",
        claim_issues=[
            ClaimIssue(
                product_id="bag_001",
                product_title="UrbanLite Commuter Backpack 22L",
                claim_type="price",
                issue_type="incorrect",
                severity="hard",
                field="price.amount",
                claimed_value=2,
                observed_value=899,
                message="price claim 2 does not match catalog price 899 CNY",
            )
        ],
    )

    result = repair_answer_from_verification(
        "I compared 2 options and recommend UrbanLite Commuter Backpack 22L.",
        report,
    )

    assert result.status == "qualified"
    assert "2 options" in result.repaired_answer
    assert result.warnings


def test_battery_repair_does_not_replace_unrelated_number_without_battery_context():
    report = VerificationReport(
        status="warning",
        claim_issues=[
            ClaimIssue(
                product_id="hp_006",
                product_title="SonicLite AirBuds",
                claim_type="battery_life",
                issue_type="incorrect",
                severity="warning",
                field="attributes.battery_life_hours",
                claimed_value=2,
                observed_value=24,
                message="battery claim 2h does not match catalog battery_life_hours=24",
            )
        ],
    )

    result = repair_answer_from_verification(
        "I compared 2 options and recommend SonicLite AirBuds.",
        report,
    )

    assert result.status == "qualified"
    assert "2 options" in result.repaired_answer
    assert result.warnings


def test_tool_calling_demo_uses_shared_repair_utility():
    import examples.integrations.tool_calling_agent_demo as demo

    assert demo.repair_or_qualify_answer.__module__ == "recharness.core.answer_repair"
