# Headphones Dogfooding Notes

## Purpose

Local notes from manually reviewing the deterministic headphones dogfooding
runner. These notes are for development quality checks, not publication-style
scoring.

## How to Run

```bash
python examples/integrations/run_headphones_dogfood.py \
  --out runs/headphones_dogfood/results.jsonl
```

## Current Observations

- All current dogfooding tasks route to the `headphones` domain.
- The deterministic loop returns grounded product ids and final answers for all tasks.
- Explicit in-stock requests should avoid out-of-stock catalog items.
- Short summaries are easier to inspect when they include product titles and issue counts.

## Follow-up Quality Fixes

- Keep availability parsing limited to clear purchase/stock wording.
- Continue expanding headphones vocabulary only when it maps to existing catalog fields.
- Keep generated `runs/` outputs local unless a future workflow explicitly needs fixtures.
