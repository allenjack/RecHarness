# MCP Configuration

The MCP integration supports single-catalog and multi-catalog modes.

Single catalog:

```bash
recharness mcp serve --catalog examples/backpacks/catalog.jsonl
```

Multi-catalog config:

```bash
recharness mcp serve --config examples/mcp/catalogs.json
```

Config files define catalog domains, paths, categories, descriptions, and an
optional default catalog. JSON always works. YAML files require PyYAML.

Tools:

- `recharness_list_catalogs`
- `recharness_parse_preferences`
- `recharness_assist`
- `recharness_verify_recommendation`

Requests use the stable schemas:

- `ParseRequest`
- `AssistRequest`
- `VerifyRequest`

Responses use stable envelopes:

- `ParseResponse`
- `AssistResponse`
- `VerifyResponse`

If routing fails, the tool returns `status="error"` and an `errors` list.
