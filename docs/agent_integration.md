# Agent Integration

RecHarness is designed to sit between a general-purpose agent and a local
product catalog.

Recommended loop:

1. List available catalogs.
2. Select the most appropriate domain.
3. Call `assist` with the user query and explicit domain.
4. Use the `RecommendationBundle` to draft an answer.
5. Call `verify` with the same explicit domain before returning the final response.
6. If status is `warning` or `fail`, repair or qualify the answer.
7. Return the grounded answer.

For best reliability, general agents should call `recharness_list_catalogs`,
choose a domain, and pass `domain` explicitly to assist and verify calls. If no
domain is provided, RecHarness tries parsed category routing and then
default-catalog fallback. That is convenient, but less reliable for ambiguous
queries.

SDK sketch:

```python
from recharness import AgentHarnessRouter, AssistRequest, VerifyRequest

router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")
catalogs = router.list_catalogs()

assist = router.assist(
    AssistRequest(
        user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
        domain="headphones",
        top_k=3,
    )
)

draft = "..."

verify = router.verify(
    VerifyRequest(
        user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
        domain="headphones",
        agent_answer=draft,
    )
)
```

Agent-facing methods return stable response envelopes. Errors are returned in
`errors` lists instead of raw Python exceptions.
