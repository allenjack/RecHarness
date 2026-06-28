# Recommendation Bundle

`RecommendationBundle` is the SDK output from `RecHarness.assist()`.

Fields:

- `user_need`: parsed `UserNeed` from the original query
- `candidates`: ranked candidate list before final bundling
- `recommended`: products selected for recommendation
- `rejected`: diagnostic products that were retrieved but should not be recommended
- `comparison_axes`: fields useful for comparing candidates
- `constraint_report`: aggregate verification report over retrieved candidates
- `clarification_questions`: optional questions for missing inputs
- `summary_for_agent`: short instruction text for a downstream agent
- `trace_id`: stable id for related trace events

Design principle:

Recommended products should pass hard constraints. Rejected products are
preserved for diagnostics, so users can see which catalog items were considered
and why they were excluded.

Minimal SDK use:

```python
from recharness import RecHarness

harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
bundle = harness.assist("Find a commuting backpack under 1500 RMB", top_k=3)

for candidate in bundle.recommended:
    print(candidate.product.title, candidate.final_score)

for candidate in bundle.rejected:
    print(candidate.product.title, candidate.violations)
```
