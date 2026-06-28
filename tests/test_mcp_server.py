from recharness.integrations.mcp_server import RecHarnessMcpTools


def test_mcp_tools_parse_preferences_returns_json_dict():
    tools = RecHarnessMcpTools.from_config_file("examples/mcp/catalogs.json")

    result = tools.parse_preferences(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
        domain="backpacks",
    )

    assert result["status"] == "ok"
    assert result["domain"] == "backpacks"
    assert result["user_need"]["category"] == "backpack"
    assert result["user_need"]["hard_constraints"][0]["field"] == "price.amount"


def test_mcp_tools_assist_returns_recommendation_bundle_dict():
    tools = RecHarnessMcpTools.from_config_file("examples/mcp/catalogs.json")

    result = tools.assist(
        user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
        domain="backpacks",
        top_k=1,
    )

    assert result["status"] in {"ok", "warning"}
    assert result["bundle"]["recommended"][0]["product"]["category"] == "backpack"
    assert result["bundle"]["recommended"][0]["violations"] == []
    assert result["bundle"]["trace_id"].startswith("assist_")


def test_mcp_tools_verify_recommendation_returns_report_dict():
    tools = RecHarnessMcpTools.from_config_file("examples/mcp/catalogs.json")

    result = tools.verify_recommendation(
        user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
        agent_answer="I recommend RainGuard Metro Pack 24L. It costs 1599 RMB.",
        domain="backpacks",
    )

    assert result["status"] == "fail"
    assert result["report"]["violations"][0]["constraint"]["field"] == "price.amount"


def test_mcp_tools_list_catalogs_and_route_headphones():
    tools = RecHarnessMcpTools.from_config_file("examples/mcp/catalogs.json")

    catalogs = tools.list_catalogs()
    result = tools.assist(
        user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
        domain="headphones",
        top_k=1,
    )

    assert catalogs["default_catalog"] == "backpacks"
    assert {item["domain"] for item in catalogs["catalogs"]} == {"backpacks", "headphones"}
    assert result["status"] in {"ok", "warning"}
    assert result["bundle"]["recommended"][0]["product"]["category"] == "headphones"
