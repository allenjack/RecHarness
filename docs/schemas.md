# Schemas

RecHarness uses Pydantic models for all public data contracts.

Core schemas:

- `ProductItem`: catalog product record with generic `attributes`
- `Money`: amount and currency
- `Evidence`: field-level product evidence
- `Constraint`: dot-path constraint such as `price.amount <= 1500`
- `Preference`: weighted soft or negative preference
- `UserNeed`: parsed user query
- `RecommendationCandidate`: scored product plus checks, risks, and evidence
- `RecommendationBundle`: assist-mode output for downstream agents
- `VerificationReport`: constraint and claim verification result
- `TraceEvent`: JSONL trace event

Catalog rows validate as `ProductItem` objects. Product-specific details should go in `attributes` so the core schema remains category-agnostic.
