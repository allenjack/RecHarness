# Changelog

## 0.1.0 - 2026-06-26

Initial v0.1 release foundation:

- Pydantic schemas for products, constraints, preferences, bundles, verification reports, and traces
- JSONL catalog loading, validation, and field coverage stats
- Rule-based preference parser for common backpack queries in English and Chinese
- Constraint verifier with dot-path field resolution
- Keyword, attribute-filter, and hybrid retrieval
- Transparent simple ranker
- `RecHarness.assist()` SDK flow
- `RecHarness.verify_agent_recommendation()` SDK flow
- CLI commands for catalog validation, assist, verify, eval, and optional MCP serving
- JSONL trace logging
- Batch evaluation runner with metrics, leaderboard, and traces
- Optional MCP integration
- Backpack example catalog, missions, and agent outputs
