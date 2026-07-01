# Tool-Calling Agent Demo

## Purpose

`examples/integrations/tool_calling_agent_demo.py` shows how a general-purpose
agent can use RecHarness through plain Python tool callables. The demo is
deterministic and does not require MCP, OpenAI, LangGraph, or external LLM APIs.

## Flow

```text
list_catalogs -> choose domain -> assist -> draft -> verify -> repair
```

The demo lists configured catalogs, chooses an explicit domain, asks RecHarness
for a grounded `RecommendationBundle`, drafts only from `bundle.recommended`,
verifies the draft, and repairs or qualifies the final answer when verification
returns warning or fail.

The demo uses the shared deterministic repair utility rather than local
string-edit logic.

## Run

```bash
python examples/integrations/tool_calling_agent_demo.py
```

## Local Dogfooding

Headphones dogfooding tasks can be run locally as a development utility for
checking routing, grounded recommendations, and verification diagnostics:

```bash
python examples/integrations/run_headphones_dogfood.py
```

Optional JSONL output:

```bash
python examples/integrations/run_headphones_dogfood.py \
  --out runs/headphones_dogfood/results.jsonl
```

This is not a benchmark report generator; it prints task-level diagnostics and
can write raw JSONL results for manual review.

## Tool Adapter

`make_recharness_tool_functions(router)` returns plain Python callables:

- `recharness_list_catalogs`
- `recharness_assist`
- `recharness_verify_recommendation`

Each callable returns a JSON-serializable `dict`. Unexpected exceptions are
converted into a stable error envelope:

```json
{"status": "error", "errors": ["..."]}
```

## What This Demonstrates

- How an agent can discover available catalogs before picking a domain.
- How to pass `domain` explicitly into assist and verify calls.
- How to draft from local catalog facts instead of unsupported model guesses.
- How to verify a candidate answer before returning it to the user.
- How to keep the whole loop deterministic for local testing.

## How To Port To A Real Agent Framework

Use:

```python
tools = make_recharness_tool_functions(router)
```

Then wrap the returned callables with the framework-specific tool mechanism.
The same functions can be adapted to OpenAI Agents SDK, LangGraph, MCP, or other
agent frameworks without changing RecHarness core logic.
