from recharness import EvalRunner, RecHarness

harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
result = EvalRunner(
    harness=harness,
    missions_path="examples/backpacks/missions.jsonl",
).run_assist(top_k=3)

print(result.metrics)
