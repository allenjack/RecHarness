from recharness import EvalRunner, JsonlCatalog, RecHarness


def test_backpack_benchmark_has_meaningful_size_and_coverage():
    catalog = JsonlCatalog.load("examples/backpacks/catalog.jsonl")
    stats = catalog.stats()

    mission_count = _line_count("examples/backpacks/missions.jsonl")
    output_count = _line_count("examples/backpacks/agent_outputs.jsonl")

    assert len(catalog) >= 50
    assert mission_count >= 50
    assert output_count >= 50
    assert stats.field_coverage["price"] >= 0.95
    assert stats.field_coverage["attributes.laptop_size_inches"] >= 0.9
    assert stats.field_coverage["attributes.water_resistance"] >= 0.9
    assert stats.field_coverage["attributes.weight_kg"] >= 0.9


def test_backpack_benchmark_eval_has_expected_signal():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
    result = EvalRunner(
        harness=harness,
        missions_path="examples/backpacks/missions.jsonl",
    ).run_with_agent_outputs("examples/backpacks/agent_outputs.jsonl")

    assert result.metrics["missions_total"] >= 50
    assert 0.65 <= result.metrics["product_groundedness_rate"] <= 0.9
    assert 0.55 <= result.metrics["hard_constraint_satisfaction_rate"] <= 0.85
    assert 0.15 <= result.metrics["unsupported_claim_rate"] <= 0.45


def _line_count(path: str) -> int:
    with open(path, encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())
