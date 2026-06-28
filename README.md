# RecHarness

RecHarness is an agent-agnostic harness for making general-purpose agents more reliable product recommenders.

General agents are becoming shopping interfaces, but they can recommend products that violate user constraints, hallucinate attributes, overfit vague preferences, or lack evidence. RecHarness provides the harness-level structure needed to make recommendation flows inspectable and testable.

The current package version is `0.1.0`. The main branch includes:

- typed product, preference, constraint, recommendation, verification, and trace schemas
- deterministic local JSONL catalog loading
- catalog validation and field coverage stats
- rule-based preference extraction for common shopping constraints
- dot-path constraint verification against product records
- structured claim verification for prices, laptop fit, water resistance, weight, and availability
- deterministic local keyword and attribute-aware retrieval
- transparent simple ranking
- `RecHarness.assist()` with recommended and rejected candidate bundles
- `verify_agent_recommendation()` SDK flow
- CLI commands for catalog validation, assist, verify, eval, eval-assist, and optional MCP serving
- JSONL trace logging
- batch evaluation
- backpack and headphones example domains
- pytest coverage for the foundation behavior

No external LLM API is required for the current deterministic harness. Retrieval
is local and catalog-based. The MCP server is optional.

## Development

The project is configured for `uv` and `hatchling`.

```bash
uv sync --extra dev
uv run pytest
```

If `uv` is unavailable, use a local virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
```

## Catalog Example

```python
from recharness import JsonlCatalog

catalog = JsonlCatalog.load("examples/backpacks/catalog.jsonl")
report = catalog.validate()
stats = catalog.stats()

print(report.product_count)
print(stats.field_coverage["price"])
```

## Parse A Shopping Need

```python
from recharness import RuleBasedPreferenceParser

parser = RuleBasedPreferenceParser()
need = parser.parse(
    "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop and is not too business."
)

print(need.hard_constraints)
print(need.negative_preferences)
```

## Verify Product Constraints

```python
from recharness import Constraint, ConstraintVerifier, Money, ProductItem

product = ProductItem(
    product_id="bag_001",
    title="UrbanLite Commuter Backpack 22L",
    category="backpack",
    price=Money(amount=899, currency="CNY"),
    attributes={"laptop_size_inches": 14, "style": ["minimal", "casual"]},
)

report = ConstraintVerifier().verify_product(
    product,
    [
        Constraint(field="price.amount", operator="<=", value=1500),
        Constraint(field="attributes.laptop_size_inches", operator=">=", value=14),
    ],
)

print(report.status)
```

## Verify An Agent Answer

```python
from recharness import RecHarness

harness = RecHarness.from_jsonl_catalog(
    "examples/backpacks/catalog.jsonl",
    trace_path="runs/assist_traces.jsonl",
)

report = harness.verify_agent_recommendation(
    user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop.",
    agent_answer="I recommend RainGuard Metro Pack 24L. It costs 1599 RMB.",
)

print(report.status)
print(report.violations)
print(report.claim_issues)
```

```bash
recharness verify \
  --catalog examples/backpacks/catalog.jsonl \
  --query "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop" \
  --answer "I recommend RainGuard Metro Pack 24L. It costs 1599 RMB."
```

```bash
recharness verify \
  --catalog examples/backpacks/catalog.jsonl \
  --query "1500元以内、防水、适合通勤的双肩包" \
  --answer "我推荐 NorthPeak Office Pack 28L，售价1299元，完全防水，而且很轻量。" \
  --json
```

```bash
recharness verify \
  --catalog examples/backpacks/catalog.jsonl \
  --query "Find a commuting backpack under 1500 RMB" \
  --answer "I recommend UrbanLite Commuter Backpack 22L. It costs 899 RMB." \
  --trace-path runs/verify.jsonl
```

## Assist Flow

```python
from recharness import RecHarness

harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

bundle = harness.assist(
    user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop and is not too business.",
    top_k=2,
)

for candidate in bundle.recommended:
    print(candidate.product.title, candidate.final_score)

print(bundle.summary_for_agent)
```

```bash
recharness assist \
  --catalog examples/backpacks/catalog.jsonl \
  --query "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop and is not too business" \
  --top-k 2
```

```bash
recharness assist \
  --catalog examples/backpacks/catalog.jsonl \
  --query "1500元以内，适合通勤，能放14寸电脑，不要太商务，最好防水、轻量的双肩包" \
  --top-k 3 \
  --json
```

```bash
recharness assist \
  --catalog examples/backpacks/catalog.jsonl \
  --query "Find a commuting backpack under 1500 RMB" \
  --trace-path runs/assist.jsonl \
  --variant full
```

## Evaluate Agent Outputs

```bash
recharness eval \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --agent-outputs examples/backpacks/agent_outputs.jsonl \
  --out runs/eval_baseline
```

The eval command writes `metrics.json`, `per_mission_results.jsonl`,
`leaderboard.csv`, and `traces.jsonl`.
Trace records include structured verification reports, including `claim_issues`
for factual claim diagnostics. Claim metrics distinguish unsupported,
overstated, and incorrect claims.

## Run Local Evaluation

RecHarness includes local evaluation utilities for checking recommendation
quality, constraint satisfaction, claim issues, and failure labels.

Use `eval-assist` to evaluate RecHarness output directly against local mission
files:

```bash
recharness eval-assist \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --out runs/assist_eval \
  --top-k 3 \
  --variant full
```

Diagnostic variants help users compare retrieval behavior:

- `full`: hybrid keyword + constraint-aware retrieval
- `keyword_only`: keyword retrieval only
- `constraint_only`: constraint-aware scoring only

```bash
recharness eval-assist \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --out runs/assist_eval_keyword \
  --top-k 3 \
  --variant keyword_only
```

```bash
recharness eval-assist \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --out runs/assist_eval_constraint \
  --top-k 3 \
  --variant constraint_only
```

Assist evaluation reports `recommendation_count_avg`,
`hard_constraint_satisfaction_rate`, `hard_violation_rate`,
`gold_recall_at_k`, `avg_final_score`, and `avg_rejected_candidates`.
Per-mission outputs include `failure_labels` such as
`product_hallucination`, `hard_constraint_violation`, `overstated_claim`,
`incorrect_claim`, and `candidate_pool_contains_violations`.

The checked-in backpack benchmark contains:

- 50 catalog products
- 50 recommendation missions
- 50 baseline agent outputs covering valid, over-budget, hallucinated, and overstated-claim answers

Example domains:

- `examples/backpacks`
- `examples/headphones`

SDK demos:

- `examples/assist_demo.py`
- `examples/verify_demo.py`
- `examples/evaluation_demo.py`

Additional docs:

- `docs/catalog_schema.md`
- `docs/recommendation_bundle.md`
- `docs/verification.md`
- `docs/evaluation.md`
- `docs/adding_a_new_domain.md`

## Current Limitations

- No real-time price or inventory lookup
- Rule-based parser covers common shopping constraints but is not comprehensive
- Chinese and English claim checks are pattern-based
- Product mention resolution is deterministic and may miss ambiguous references
- No checkout, payment, or order workflow
- No high-risk product suitability checking

## MCP Server

The MCP integration is optional:

```bash
uv sync --extra dev --extra mcp

recharness mcp serve \
  --catalog examples/backpacks/catalog.jsonl
```

The MCP server exposes tools for preference parsing, assist-mode bundles, and recommendation verification.

Catalog rows are JSON objects that validate as `ProductItem` records:

```json
{"product_id":"bag_001","title":"UrbanLite Commuter Backpack 22L","category":"backpack","price":{"amount":899,"currency":"CNY"},"attributes":{"laptop_size_inches":14,"weight_kg":0.85}}
```

## License

MIT
