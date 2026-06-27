# Changelog

## Unreleased

Structured verification depth:

- Added bundle construction that separates recommended candidates from rejected hard-violation candidates
- Made `RecommendationBundle.constraint_report` required
- Changed retrieval from hard filtering to soft constraint-aware scoring
- Added explicit product resolution fields to `VerificationReport`
- Added `ClaimIssue` and `VerificationReport.claim_issues` for typed claim diagnostics
- Added product identity and issue type fields to claim issues
- Kept `VerificationReport.unsupported_claims` as a compatibility list of issue messages
- Expanded claim verification for price, laptop fit, water resistance, weight, and availability claims
- Added Chinese claim checks for waterproof, lightweight, availability, and laptop-fit claims
- Made claim verification product-local for multi-product answers
- Made hard factual claim issues fail recommendation verification
- Expanded rule-based parsing for more categories, scenarios, water resistance, weight, and capacity
- Added CLI `--json`, `--trace-path`, and `--no-fail-on-warning` options
- Added verify-mode trace events
- Expanded evaluation records and metrics with groundedness, hallucination, hard-violation, claim-accuracy, and average-count fields
- Added structured claim issue output to `recharness verify`
- Documented claim issues in schemas, evaluation traces, and README usage

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
