# Catalog Schema

RecHarness catalogs are JSONL files. Each line is one `ProductItem`.

Required fields:

- `product_id`: stable unique product id
- `title`: product title used for mention resolution
- `category`: product category such as `backpack` or `headphones`

Common optional fields:

- `brand`: product brand
- `price`: `Money` object with `amount` and three-letter `currency`
- `availability`: `in_stock`, `out_of_stock`, or `unknown`
- `attributes`: category-specific product facts
- `tags`: searchable labels
- `description`: searchable product description
- `review_summary`: short review-derived summary
- `evidence`: list of field-level `Evidence` records
- `source`: catalog or merchant source id

`Money`:

- `amount`: non-negative number
- `currency`: three-letter currency code normalized to uppercase

`Evidence`:

- `field`: dot-path field such as `attributes.weight_kg`
- `value`: observed value
- `source_type`: source label such as `catalog`
- `source`: optional source location
- `confidence`: optional value from `0` to `1`

Put category-specific facts in `attributes` so the core schema stays reusable.
Examples include `laptop_size_inches`, `weight_kg`, `noise_cancellation`,
`battery_life_hours`, and `latency_ms`.

Example JSONL row:

```json
{"product_id":"bag_001","title":"UrbanLite Commuter Backpack 22L","category":"backpack","price":{"amount":899,"currency":"CNY"},"availability":"in_stock","attributes":{"laptop_size_inches":14,"weight_kg":0.85,"water_resistance":"water_resistant"}}
```

Validate a catalog:

```bash
recharness catalog validate examples/backpacks/catalog.jsonl
```
