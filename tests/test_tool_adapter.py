from recharness import AgentHarnessRouter
from recharness.integrations import make_recharness_tool_functions


def test_tool_adapter_exposes_plain_json_serializable_callables():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

    tools = make_recharness_tool_functions(router)
    catalogs = tools["recharness_list_catalogs"]()
    assist = tools["recharness_assist"](
        user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
        domain="headphones",
        top_k=1,
    )
    verify = tools["recharness_verify_recommendation"](
        user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
        domain="headphones",
        agent_answer="我推荐 SonicLite AirBuds，售价699元，有主动降噪。",
    )

    assert set(tools) == {
        "recharness_list_catalogs",
        "recharness_assist",
        "recharness_verify_recommendation",
    }
    assert catalogs["default_catalog"] == "backpacks"
    assert assist["domain"] == "headphones"
    assert assist["bundle"]["recommended"][0]["product"]["category"] == "headphones"
    assert verify["status"] == "warning"
    assert verify["report"]["claim_issues"][0]["claim_type"] == "noise_cancellation"


def test_tool_adapter_returns_stable_error_dict_for_unexpected_failures():
    class BrokenRouter:
        def list_catalogs(self):
            raise RuntimeError("catalog unavailable")

    tools = make_recharness_tool_functions(BrokenRouter())

    result = tools["recharness_list_catalogs"]()

    assert result == {"status": "error", "errors": ["catalog unavailable"]}
