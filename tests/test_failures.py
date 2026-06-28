from recharness import RecHarness
from recharness.evaluation.failures import failure_labels_from_bundle, failure_labels_from_report


def test_failure_labels_for_hallucinated_product():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
    report = harness.verify_agent_recommendation(
        "Find a commuting backpack under 1500 RMB",
        "I recommend PhantomPack Air 25L. It costs 999 RMB.",
    )

    labels = failure_labels_from_report(report)

    assert "product_hallucination" in labels
    assert "no_grounded_product" in labels


def test_failure_labels_for_overstated_and_incorrect_claims():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
    overstated = harness.verify_agent_recommendation(
        "Find a commuting backpack under 1500 RMB",
        "I recommend NorthPeak Office Pack 28L. It costs 1299 RMB and is fully waterproof.",
    )
    incorrect = harness.verify_agent_recommendation(
        "Find a commuting backpack under 1500 RMB",
        "I recommend UrbanLite Commuter Backpack 22L. It costs 699 RMB.",
    )

    assert "overstated_claim" in failure_labels_from_report(overstated)
    assert "incorrect_claim" in failure_labels_from_report(incorrect)


def test_failure_labels_for_assist_bundle_with_rejected_candidates():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
    bundle = harness.assist(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
        top_k=2,
    )

    labels = failure_labels_from_bundle(bundle)

    assert "candidate_pool_contains_violations" in labels
    assert "rejected_candidate_present" in labels
