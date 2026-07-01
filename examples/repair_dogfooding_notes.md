# Repair Dogfooding Notes

## Purpose

Local development notes for checking whether deterministic repair is useful and safe.

This is not a benchmark report.

## How to Run

```bash
python examples/integrations/run_repair_dogfood.py
```

Optional output:

```bash
python examples/integrations/run_repair_dogfood.py \
  --out runs/repair_dogfood/results.jsonl
```

Run one fixture file:

```bash
python examples/integrations/run_repair_dogfood.py \
  --tasks examples/headphones/edge_cases.jsonl
```

## Current Observations

- Standard headphones dogfood tasks mostly pass verification and remain `unchanged`.
- Impossible-budget cases with no safe assist candidate are `qualified`.
- Inventory-conflict and hard-constraint cases can be `repaired` by replacing with a safe recommended candidate.
- The microphone-noise-reduction edge case is repaired without claiming active noise cancellation.
- Repair output keeps local catalog grounding through repair changes and warnings.

## Follow-up Fixes

- Fixed the microphone-noise-reduction edge case so repair no longer leaves `active noise cancellation` wording in the final answer.
