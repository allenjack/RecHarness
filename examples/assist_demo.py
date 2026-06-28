from recharness import RecHarness

harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
bundle = harness.assist(
    "1500元以内，适合通勤，能放14寸电脑，不要太商务，最好防水、轻量的双肩包",
    top_k=3,
)

for candidate in bundle.recommended:
    print(candidate.product.title, candidate.final_score)

print(bundle.summary_for_agent)
