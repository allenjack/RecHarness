from recharness import AgentHarnessRouter, AssistRequest, VerifyRequest
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


def test_tool_calling_demo_uses_shared_repair_utility():
    import examples.integrations.tool_calling_agent_demo as demo

    assert demo.repair_or_qualify_answer.__module__ == "recharness.core.answer_repair"
