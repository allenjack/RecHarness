# Domain Adapters

Domain adapters add deterministic category-specific behavior without requiring
external services.

Use an adapter when a category needs:

- extra query enrichment after generic parsing
- domain-specific claim checks
- category vocabulary that should not be hard-coded into generic components

Adapter interface:

```python
class DomainAdapter:
    category: str

    def enrich_user_need(self, need, query):
        ...

    def verify_claims(self, product, text):
        ...
```

`enrich_user_need()` can add constraints, preferences, or scenarios.
`verify_claims()` can add `ClaimIssue` records for category-specific claims.

The headphones adapter detects wireless/wired needs, ANC, low latency, battery
life, sweat resistance, and common use cases such as office, commute, running,
gaming, travel, study, and studio listening.
