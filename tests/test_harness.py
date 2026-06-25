from recharness import RecHarness


def test_recharness_assist_returns_recommendation_bundle_for_example_catalog():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    bundle = harness.assist(
        user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop and is not too business",
        top_k=2,
    )

    assert bundle.user_need.category == "backpack"
    assert [candidate.product.product_id for candidate in bundle.recommended] == [
        "bag_001",
        "bag_002",
    ]
    assert bundle.recommended[0].final_score is not None
    assert bundle.rejected == []
    assert "UrbanLite" in bundle.summary_for_agent
    assert bundle.trace_id.startswith("assist_")
