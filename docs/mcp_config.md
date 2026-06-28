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

Recommended MCP flow:

1. Call `recharness_list_catalogs`.
2. Select the most appropriate domain.
3. Call `recharness_assist(user_query="...", domain="headphones")`.
4. Draft the answer from the returned bundle.
5. Call `recharness_verify_recommendation(user_query="...", domain="headphones", agent_answer="...")`.

For best reliability, agents should pass `domain` explicitly. If no domain is
provided, RecHarness tries parsed category routing and then default-catalog
fallback. This fallback is useful for convenience but can be less reliable for
ambiguous queries.

Requests use the stable schemas:

- `ParseRequest`
- `AssistRequest`
- `VerifyRequest`

Responses use stable envelopes:

- `ParseResponse`
- `AssistResponse`
- `VerifyResponse`

If routing fails, the tool returns `status="error"` and an `errors` list.
