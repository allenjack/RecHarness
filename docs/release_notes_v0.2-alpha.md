# RecHarness v0.2-alpha Release Notes

RecHarness v0.2-alpha focuses on making the harness callable by general-purpose agents.

## Highlights

- Agent-facing parse, assist, and verify schemas
- Multi-catalog `AgentHarnessRouter`
- MCP tools for catalog listing, parsing, assist, and verification
- Framework-neutral tool callables via `make_recharness_tool_functions()`
- Deterministic MCP-style and tool-calling agent-loop demos
- Headphones domain adapter and local dogfooding utilities
- Safer local-catalog-based answer drafting
- Local evaluation and diagnostics

## What RecHarness Is

RecHarness is an agent-agnostic recommendation quality layer. It helps agents ground product recommendations in local catalogs, verify constraints and claims, and inspect recommendation traces.

## What RecHarness Is Not

- Not a full shopping agent
- Not a checkout system
- Not a real-time ecommerce crawler
- Not dependent on an external LLM API
- Not a benchmark report generator for research papers

## Quick Checks

```bash
uv run ruff check .
uv run pytest
uv build
python examples/integrations/tool_calling_agent_demo.py
python examples/integrations/run_headphones_dogfood.py
```
