# Evaluation

RecHarness includes local evaluation utilities for checking recommendation
quality, constraint satisfaction, claim issues, and failure labels.

## Saved Agent Outputs

Use `eval` when you have saved answers from an external agent:

```bash
recharness eval \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --agent-outputs examples/backpacks/agent_outputs.jsonl \
  --out runs/eval_baseline
```

Input files:

- `catalog.jsonl`: local product catalog
- `missions.jsonl`: mission id, user query, optional gold product ids
- `agent_outputs.jsonl`: mission id, agent name, answer text

## RecHarness Assist Outputs

Use `eval-assist` to evaluate RecHarness recommendations directly:

```bash
recharness eval-assist \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --out runs/assist_eval \
  --top-k 3 \
  --variant full
```

Diagnostic variants help users compare retrieval behavior:

- `full`: hybrid keyword + constraint-aware retrieval
- `keyword_only`: keyword retrieval only
- `constraint_only`: constraint-aware scoring only

## Output Files

Both evaluation modes write:

- `metrics.json`: aggregate metrics
- `per_mission_results.jsonl`: compact per-mission results
- `leaderboard.csv`: metrics grouped by agent name
- `traces.jsonl`: per-mission records with verification details

Saved-answer metrics include:

- `product_groundedness_rate`
- `hallucinated_product_rate`
- `hard_constraint_satisfaction_rate`
- `hard_violation_rate`
- `claim_accuracy_rate`
- `claim_issue_rate`
- `unsupported_claim_rate`
- `overstated_claim_rate`
- `incorrect_claim_rate`
- `verification_pass_rate`
- `avg_violations_per_answer`
- `avg_claim_issues_per_answer`

Assist metrics include:

- `recommendation_count_avg`
- `hard_constraint_satisfaction_rate`
- `hard_violation_rate`
- `gold_recall_at_k`
- `avg_final_score`
- `avg_rejected_candidates`

Failure label rates are added when labels appear in the evaluated records.
