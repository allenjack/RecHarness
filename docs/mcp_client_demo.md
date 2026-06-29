# MCP Client Demo

## Purpose

`examples/integrations/mcp_client_demo.py` mirrors how a general agent would use
RecHarness tools over MCP, but it runs locally through `AgentHarnessRouter`.
This keeps the example deterministic and testable without a running MCP server
or external model.

## Flow

1. List catalogs.
2. Select a domain deterministically.
3. Call assist with the user query and explicit domain.
4. Draft an answer from `RecommendationBundle.recommended`.
5. Call verify with the same domain.
6. Return the answer, repairing or qualifying it when verification reports an issue.

## Run

```bash
python examples/integrations/mcp_client_demo.py
```

## What The Demo Shows

- How a general agent can use RecHarness before drafting a recommendation.
- How to avoid unsupported claims by drafting only from bundle fields.
- How to verify before returning the final answer.
- How to keep integration tests local and deterministic.

## How This Maps To MCP Tools

| Local demo call | MCP tool |
| --- | --- |
| `router.list_catalogs()` | `recharness_list_catalogs` |
| `router.assist(...)` | `recharness_assist` |
| `router.verify(...)` | `recharness_verify_recommendation` |
