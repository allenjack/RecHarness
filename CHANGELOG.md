# Changelog

## Unreleased

- Added deterministic answer repair utility and `RepairResult`.
- Added v0.3-alpha planning, repair, and agent-loop contract docs.
- Refactored deterministic demos to use the shared repair utility.
- Stabilized repair priority, language-aware repair notes, contextual numeric fixes, and `verify --repair-top-k`.
- Added local repair dogfooding runner and development notes for existing backpack and headphones fixtures.

## [0.2.0-alpha] - 2026-06-30

### Added

- Agent-facing request/response schemas for assist, verify, and parse flows.
- Multi-catalog `AgentHarnessRouter`.
- Multi-catalog MCP tool support.
- Framework-neutral tool adapter via `make_recharness_tool_functions()`.
- Deterministic MCP-style and tool-calling agent demos.
- Headphones domain adapter with vocabulary for ANC, wired/wireless, TWS, calls, workout, sweat resistance, latency, and battery life.
- Headphones dogfooding tasks and local dogfood runner.
- Local dogfooding notes for development quality review.

### Improved

- Safer answer drafting with local catalog wording.
- More precise availability parsing for in-stock requests.
- Headphones claim verification and product-title substring handling.
- Dogfood diagnostics with recommended titles and issue counts.

### Notes

- Python package metadata uses the PEP 440 version `0.2.0a0` for this alpha release.
- No external LLM dependency is required.
- Dogfooding utilities are local development tools, not benchmark report generators.

## 0.1.0 - Initial alpha

- Local JSONL product catalog loading and validation
- Structured product, preference, constraint, recommendation, and verification schemas
- Rule-based preference parsing
- Keyword, constraint-aware, and hybrid retrieval
- Constraint verification
- Product-local claim verification
- RecommendationBundle with recommended and rejected candidates
- Assist and verify SDK flows
- CLI for catalog validation, assist, verify, eval, and eval-assist
- JSONL tracing
- Optional MCP server
- Backpack and headphones example domains
