# RecHarness

RecHarness is an agent-agnostic harness for making general-purpose agents more reliable product recommenders.

General agents are becoming shopping interfaces, but they can recommend products that violate user constraints, hallucinate attributes, overfit vague preferences, or lack evidence. RecHarness provides the harness-level structure needed to make recommendation flows inspectable and testable.

This v0.2 development version includes:

- typed product, preference, constraint, recommendation, verification, and trace schemas
- deterministic local JSONL catalog loading
- catalog validation and field coverage stats
- rule-based preference extraction for common shopping constraints
- dot-path constraint verification against product records
- structured claim verification for prices, laptop fit, water resistance, weight, and availability
- deterministic keyword and attribute-filter retrieval
- transparent simple ranking
- `RecHarness.assist()` and `verify_agent_recommendation()` SDK flows
- CLI commands for catalog validation, assist, verify, eval, and optional MCP serving
- JSONL trace logging
- batch evaluation
- a 50-product, 50-mission backpack benchmark fixture
- pytest coverage for the foundation behavior

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

## Evaluate Agent Outputs

```bash
recharness eval \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --agent-outputs examples/backpacks/agent_outputs.jsonl \
  --out runs/eval_baseline
```

The eval command writes `metrics.json`, `leaderboard.csv`, and `traces.jsonl`.
Trace records include structured verification reports, including `claim_issues`
for factual claim diagnostics.

The checked-in backpack benchmark contains:

- 50 catalog products
- 50 recommendation missions
- 50 baseline agent outputs covering valid, over-budget, hallucinated, and overstated-claim answers

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
