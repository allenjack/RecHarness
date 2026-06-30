# Release Checklist

## Before Tagging

- [ ] `uv run ruff check .`
- [ ] `uv run pytest`
- [ ] `uv build`
- [ ] `python examples/integrations/mcp_client_demo.py`
- [ ] `python examples/integrations/tool_calling_agent_demo.py`
- [ ] `python examples/integrations/run_headphones_dogfood.py`
- [ ] Confirm generated `runs/` output is not committed.
- [ ] Confirm no external LLM credentials are required.
- [ ] Confirm README, CHANGELOG, and docs are up to date.

## v0.2-alpha Scope

- Agent-facing schemas
- Multi-catalog router
- MCP tools
- Tool adapter
- Agent-loop demos
- Headphones adapter
- Local dogfooding utilities

## Out of Scope

- Real-time ecommerce crawling
- Checkout
- External LLM dependency
- Production deployment
- Research-only report generation
- New product domains
