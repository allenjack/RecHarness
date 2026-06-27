from recharness import RecHarness


def test_verify_agent_recommendation_reports_hard_constraint_violation():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    report = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
        agent_answer=(
            "I recommend RainGuard Metro Pack 24L. It costs 1599 RMB "
            "and fits a 15-inch laptop."
        ),
    )

    assert report.status == "fail"
    assert any(
        violation.constraint.field == "price.amount"
        and violation.observed_value == 1599
        for violation in report.violations
    )
    assert any("RainGuard Metro Pack 24L" in suggestion for suggestion in report.repair_suggestions)
    assert report.product_grounded is True
    assert [product.product_id for product in report.resolved_products] == ["bag_003"]
    assert report.unresolved_mentions == []


def test_verify_agent_recommendation_reports_overstated_waterproof_claim():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    report = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer=(
            "I recommend NorthPeak Office Pack 28L. It costs 1299 RMB "
            "and is fully waterproof."
        ),
    )

    assert report.status == "warning"
    assert any("waterproof" in claim.lower() for claim in report.unsupported_claims)
    assert any("splash_resistant" in claim for claim in report.unsupported_claims)
    assert report.claim_issues[0].claim_type == "water_resistance"
    assert report.claim_issues[0].observed_value == "splash_resistant"


def test_verify_agent_recommendation_passes_grounded_answer():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    report = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
        agent_answer=(
            "I recommend UrbanLite Commuter Backpack 22L. It costs 899 RMB "
            "and fits a 14-inch laptop."
        ),
    )

    assert report.status == "pass"
    assert report.violations == []
    assert report.unsupported_claims == []
    assert report.claim_issues == []


def test_verify_agent_recommendation_fails_on_hard_claim_issue():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    report = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer=(
            "I recommend UrbanLite Commuter Backpack 22L. It costs 699 RMB "
            "and is in stock."
        ),
    )

    assert report.status == "fail"
    assert any(issue.claim_type == "price" for issue in report.claim_issues)


def test_verify_agent_recommendation_checks_claims_against_product_local_text():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    report = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer=(
            "UrbanLite Commuter Backpack 22L costs 899 RMB. "
            "NorthPeak Office Pack 28L costs 1299 RMB."
        ),
    )

    assert report.status == "pass"
    assert report.claim_issues == []


def test_verify_agent_recommendation_only_applies_waterproof_claim_to_local_product():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    report = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer=(
            "UrbanLite Commuter Backpack 22L costs 899 RMB. "
            "NorthPeak Office Pack 28L is fully waterproof."
        ),
    )

    assert report.status == "warning"
    assert [issue.product_id for issue in report.claim_issues] == ["bag_002"]


def test_verify_agent_recommendation_resolves_partial_title_and_product_id():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    partial_report = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer="I recommend UrbanLite Commuter. It costs 899 RMB.",
    )
    product_id_report = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer="I recommend bag_001. It costs 899 RMB.",
    )

    assert [product.product_id for product in partial_report.resolved_products] == ["bag_001"]
    assert [product.product_id for product in product_id_report.resolved_products] == ["bag_001"]
    assert partial_report.product_grounded is True
    assert product_id_report.product_grounded is True


def test_verify_agent_recommendation_reports_unresolved_hallucinated_product():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    report = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer="I recommend PhantomPack Air 25L. It costs 999 RMB and is waterproof.",
    )

    assert report.status == "fail"
    assert report.product_grounded is False
    assert report.resolved_products == []
    assert "PhantomPack Air 25L" in report.unresolved_mentions


def test_verify_agent_recommendation_resolves_lowercase_and_chinese_recommendation_phrases():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    lowercase = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer="i recommend urbanlite commuter. it costs 899 RMB.",
    )
    product_id = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer="我推荐 bag_001，售价899元。",
    )

    assert [product.product_id for product in lowercase.resolved_products] == ["bag_001"]
    assert [product.product_id for product in product_id.resolved_products] == ["bag_001"]


def test_verify_agent_recommendation_reports_lowercase_and_chinese_unresolved_mentions():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    lowercase = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer="i recommend phantompack air 25l. it costs 999 RMB.",
    )
    chinese = harness.verify_agent_recommendation(
        user_query="Find a commuting backpack under 1500 RMB",
        agent_answer="我推荐 城市通勤包，售价999元。",
    )

    assert "phantompack air 25l" in lowercase.unresolved_mentions
    assert "城市通勤包" in chinese.unresolved_mentions


def test_verify_agent_recommendation_checks_chinese_claims_product_locally():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    report = harness.verify_agent_recommendation(
        user_query="1500元以内、防水、适合通勤的双肩包",
        agent_answer=(
            "UrbanLite Commuter Backpack 22L 售价899元。"
            "NorthPeak Office Pack 28L 完全防水，而且很轻量。"
        ),
    )

    assert report.status == "warning"
    assert {issue.product_id for issue in report.claim_issues} == {"bag_002"}
    assert {issue.claim_type for issue in report.claim_issues} == {
        "water_resistance",
        "weight",
    }
