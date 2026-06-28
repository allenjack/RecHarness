from recharness import AgentHarnessRouter, AssistRequest, VerifyRequest


def test_agent_facing_router_contract_smoke():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

    assist = router.assist(
        AssistRequest(
            user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
            domain="headphones",
            top_k=3,
        )
    )

    assert assist.status in {"ok", "warning"}
    assert assist.bundle is not None
    assert assist.domain == "headphones"

    verify = router.verify(
        VerifyRequest(
            user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
            domain="headphones",
            agent_answer="我推荐 SonicLite AirBuds，售价699元，有主动降噪。",
        )
    )

    assert verify.status == "warning"
    assert verify.report is not None
    assert verify.report.overstated_claims
