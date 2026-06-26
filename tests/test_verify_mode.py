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
