# Adding A New Domain

Use a new example domain when you want to exercise RecHarness on another
product category.

Steps:

1. Create `catalog.jsonl` with one `ProductItem` per line.
2. Create `missions.jsonl` with representative user queries.
3. Add `agent_outputs.jsonl` if you want to evaluate saved agent answers.
4. Run catalog validation.
5. Run `assist` for a few queries.
6. Run `eval` or `eval-assist`.
7. Add parser rules only when necessary.

Suggested folder layout:

```text
examples/my_domain/
  catalog.jsonl
  missions.jsonl
  agent_outputs.jsonl
```

Validation:

```bash
recharness catalog validate examples/my_domain/catalog.jsonl
```

Assist:

```bash
recharness assist \
  --catalog examples/my_domain/catalog.jsonl \
  --query "Find an in-stock option under 1000 RMB" \
  --top-k 3
```

Saved-answer evaluation:

```bash
recharness eval \
  --catalog examples/my_domain/catalog.jsonl \
  --missions examples/my_domain/missions.jsonl \
  --agent-outputs examples/my_domain/agent_outputs.jsonl \
  --out runs/my_domain_eval
```

Direct harness evaluation:

```bash
recharness eval-assist \
  --catalog examples/my_domain/catalog.jsonl \
  --missions examples/my_domain/missions.jsonl \
  --out runs/my_domain_assist_eval
```
