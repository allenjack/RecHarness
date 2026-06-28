# Changelog

## Unreleased

- Added stable agent-facing parse, assist, and verify request/response schemas
- Added multi-catalog configuration loading
- Added `AgentHarnessRouter` for deterministic domain routing
- Upgraded MCP adapter to support multi-catalog config mode
- Added deterministic domain adapter interface
- Added headphones query enrichment and claim checks
- Added agent-loop SDK examples and integration docs

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
