# Quickstart

Install RecHarness in development mode:

```bash
uv sync --extra dev
```

Validate the example catalog:

```bash
uv run recharness catalog validate examples/backpacks/catalog.jsonl
```

Run assist mode:

```bash
uv run recharness assist \
  --catalog examples/backpacks/catalog.jsonl \
  --query "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop and is not too business" \
  --top-k 2
```

Verify an agent answer:

```bash
uv run recharness verify \
  --catalog examples/backpacks/catalog.jsonl \
  --query "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop" \
  --answer "I recommend RainGuard Metro Pack 24L. It costs 1599 RMB."
```

Run evaluation:

```bash
uv run recharness eval \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --agent-outputs examples/backpacks/agent_outputs.jsonl \
  --out runs/eval_baseline
```
