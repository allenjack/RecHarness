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
- `traces.jsonl`: per-mission verification records

Current metrics:

- `product_groundedness_rate`
- `hard_constraint_satisfaction_rate`
- `unsupported_claim_rate`

Expected baseline fixture metrics:

```json
{
  "missions_total": 50,
  "product_groundedness_rate": 0.9,
  "hard_constraint_satisfaction_rate": 0.7,
  "unsupported_claim_rate": 0.2
}
```
