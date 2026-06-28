import pytest

from recharness import RecHarness


def test_recharness_assist_returns_recommendation_bundle_for_example_catalog():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    bundle = harness.assist(
        user_query=(
            "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop "
            "and is not too business"
        ),
        top_k=2,
    )

    assert bundle.user_need.category == "backpack"
    assert len(bundle.recommended) == 2
    assert bundle.recommended[0].product.product_id == "bag_001"
    assert all(candidate.violations == [] for candidate in bundle.recommended)
    assert bundle.recommended[0].final_score is not None
    assert bundle.constraint_report is not None
    assert bundle.constraint_report.status == "fail"
    assert any(
        candidate.product.product_id == "bag_003"
        for candidate in bundle.rejected
    )
    assert all(
        not any(violation.severity == "hard" for violation in candidate.violations)
        for candidate in bundle.recommended
    )
    assert any(bundle.constraint_report.violations)
    assert "waterproof" in bundle.summary_for_agent
    assert "UrbanLite" in bundle.summary_for_agent
    assert bundle.trace_id.startswith("assist_")


def test_recharness_variants_run_and_unknown_variant_fails():
    full = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl", variant="full")
    keyword = RecHarness.from_jsonl_catalog(
        "examples/backpacks/catalog.jsonl",
        variant="keyword_only",
    )
    constraint = RecHarness.from_jsonl_catalog(
        "examples/backpacks/catalog.jsonl",
        variant="constraint_only",
    )

    query = "Find a commuting backpack under 1500 RMB"

    assert full.assist(query, top_k=1).recommended
    assert keyword.assist(query, top_k=1).recommended
    assert constraint.assist(query, top_k=1).recommended

    with pytest.raises(ValueError, match="Unknown harness variant"):
        RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl", variant="unknown")
