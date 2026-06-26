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
- `ClaimIssue`: structured factual claim diagnostic with type, severity, field, claimed value, observed value, and message
- `VerificationReport`: constraint and claim verification result
- `TraceEvent`: JSONL trace event

Catalog rows validate as `ProductItem` objects. Product-specific details should go in `attributes` so the core schema remains category-agnostic.

`VerificationReport.claim_issues` is the primary structured claim-verification
surface. `VerificationReport.unsupported_claims` remains available as a
backward-compatible list of claim issue messages.
