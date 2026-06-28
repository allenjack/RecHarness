# Verification

`verify_agent_recommendation()` checks a free-form agent answer against a local
catalog and a parsed user query.

It verifies:

- product grounding: mentioned products resolve to catalog records
- hard constraints: resolved products satisfy parsed hard constraints
- factual claims: high-signal claims match catalog fields
- repair suggestions: actionable messages for failing or risky answers
- failure labels: compact labels for local evaluation diagnostics

Example:

```python
from recharness import RecHarness

harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
report = harness.verify_agent_recommendation(
    user_query="Find a commuting backpack under 1500 RMB",
    agent_answer="I recommend UrbanLite Commuter Backpack 22L. It costs 899 RMB.",
)

print(report.status)
print(report.claim_issues)
```

Claim issue buckets:

- `claim_issue_messages`: all claim issue messages
- `unsupported_claims`: claims not supported by catalog evidence
- `overstated_claims`: claims that exaggerate a catalog value
- `incorrect_claims`: claims that contradict a catalog value

Structured claim issues are available in `report.claim_issues`. Each issue
includes `claim_type`, `issue_type`, `severity`, `field`, `claimed_value`,
`observed_value`, and `message`.

Common failure labels:

- `product_hallucination`
- `no_grounded_product`
- `hard_constraint_violation`
- `unsupported_claim`
- `overstated_claim`
- `incorrect_claim`
- `candidate_pool_contains_violations`
- `rejected_candidate_present`
