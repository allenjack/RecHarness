from examples.integrations.mcp_client_demo import (
    draft_answer_from_bundle,
    run_demo,
    select_domain,
)


def test_mcp_client_demo_runs_without_mcp_or_llm():
    answer = run_demo("想找1000元以内，适合通勤，有降噪的蓝牙耳机")

    assert "推荐" in answer or "我建议" in answer
    assert "SonicLite AirBuds，有主动降噪" not in answer


def test_mcp_client_demo_selects_domain_deterministically():
    catalogs = {
        "default_catalog": "backpacks",
        "catalogs": [
            {"domain": "backpacks"},
            {"domain": "headphones"},
        ],
    }

    assert select_domain(catalogs, "想找有降噪的蓝牙耳机") == "headphones"
    assert select_domain(catalogs, "Find a commuting backpack") == "backpacks"
    assert select_domain(catalogs, "Find something affordable") == "backpacks"


def test_mcp_client_demo_drafts_only_from_bundle_fields():
    from recharness import AgentHarnessRouter, AssistRequest

    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")
    assist = router.assist(
        AssistRequest(
            user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
            domain="headphones",
            top_k=1,
        )
    )

    answer = draft_answer_from_bundle(assist.bundle)

    assert assist.bundle is not None
    assert assist.bundle.recommended[0].product.title in answer
    assert "主动降噪" not in answer


def test_openai_agents_demo_imports_without_agents_dependency():
    import examples.integrations.openai_agents_demo as demo

    assert hasattr(demo, "main")
