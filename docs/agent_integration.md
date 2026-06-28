# Agent Integration

RecHarness is designed to sit between a general-purpose agent and a local
product catalog.

Recommended loop:

1. Call `assist` with the user query.
2. Use the `RecommendationBundle` to draft an answer.
3. Call `verify` before returning the final response.
4. If status is `warning` or `fail`, repair or qualify the answer.
5. Return the grounded answer.

SDK sketch:

```python
from recharness import AgentHarnessRouter, AssistRequest, VerifyRequest

router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

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
