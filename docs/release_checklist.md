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
- [ ] Confirm `docs/release_notes_v0.2-alpha.md` is up to date.

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

## v0.2-alpha Checklist Run

Date: 2026-06-30

Results:

- `uv run ruff check .`: fail (`uv` was not available in this shell)
- `uv run pytest`: fail (`uv` was not available in this shell)
- `uv build`: fail (`uv` was not available in this shell)
- `python examples/integrations/mcp_client_demo.py`: fail (`python` was not the project virtual environment and could not import `recharness`)
- `python examples/integrations/tool_calling_agent_demo.py`: fail (`python` was not the project virtual environment and could not import `recharness`)
- `python examples/integrations/run_headphones_dogfood.py`: fail (`python` was not the project virtual environment and could not import `recharness`)

Notes:

- Equivalent local virtualenv checks passed:
  - `.venv/bin/python -m ruff check .`
  - `.venv/bin/python -m pytest`
  - `.venv/bin/python -m pip wheel . -w /private/tmp/recharness-wheel`
  - `.venv/bin/python examples/integrations/mcp_client_demo.py`
  - `.venv/bin/python examples/integrations/tool_calling_agent_demo.py`
  - `.venv/bin/python examples/integrations/run_headphones_dogfood.py`
- Generated `runs/` output was not committed.
- No external LLM credentials were required.
