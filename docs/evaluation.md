# Evaluation

The evaluation runner compares saved agent outputs against mission files.

The checked-in backpack benchmark is intentionally small enough for fast CI but large enough to show meaningful signal:

- 50 products in `examples/backpacks/catalog.jsonl`
- 50 missions in `examples/backpacks/missions.jsonl`
- 50 baseline outputs in `examples/backpacks/agent_outputs.jsonl`

Inputs:

- `catalog.jsonl`: local product catalog
- `missions.jsonl`: mission id, user query, optional gold product ids
- `agent_outputs.jsonl`: mission id, agent name, answer text

Command:

```bash
recharness eval \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --agent-outputs examples/backpacks/agent_outputs.jsonl \
  --out runs/eval_baseline
```

Outputs:

- `metrics.json`: aggregate rates
- `leaderboard.csv`: per-agent metrics
- `traces.jsonl`: per-mission verification records, including structured `claim_issues`

Current metrics:

- `product_groundedness_rate`
- `hallucinated_product_rate`
- `hard_constraint_satisfaction_rate`
- `hard_violation_rate`
- `claim_accuracy_rate`
- `unsupported_claim_rate`
- `overstated_claim_rate`
- `verification_pass_rate`
- `avg_violations_per_answer`
- `avg_claim_issues_per_answer`

`unsupported_claim_rate` remains a compatibility metric based on the derived
claim-message list. Use `report.claim_issues` in traces when you need typed
claim diagnostics such as price mismatch, laptop-fit overclaim, availability
overclaim, or water-resistance overstatement.

Expected baseline fixture metrics:

```json
{
  "missions_total": 50,
  "product_groundedness_rate": 0.9,
  "hallucinated_product_rate": 0.1,
  "hard_constraint_satisfaction_rate": 0.8,
  "hard_violation_rate": 0.2,
  "claim_accuracy_rate": 0.8,
  "unsupported_claim_rate": 0.2,
  "overstated_claim_rate": 0.2,
  "verification_pass_rate": 0.5,
  "avg_violations_per_answer": 0.26,
  "avg_claim_issues_per_answer": 0.2
}
```
