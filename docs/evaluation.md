# Evaluation

The evaluation runner compares saved agent outputs against mission files.

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
