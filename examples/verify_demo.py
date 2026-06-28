from recharness import RecHarness

harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
report = harness.verify_agent_recommendation(
    user_query="1500元以内、防水、适合通勤的双肩包",
    agent_answer="我推荐 NorthPeak Office Pack 28L，售价1299元，完全防水，而且很轻量。",
)

print(report.status)
print(report.overstated_claims)
print(report.incorrect_claims)
