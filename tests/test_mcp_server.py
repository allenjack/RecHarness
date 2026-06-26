from recharness.integrations.mcp_server import RecHarnessMcpTools


def test_mcp_tools_parse_preferences_returns_json_dict():
    tools = RecHarnessMcpTools.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    result = tools.parse_preferences(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop"
    )

    assert result["category"] == "backpack"
    assert result["hard_constraints"][0]["field"] == "price.amount"


def test_mcp_tools_assist_returns_recommendation_bundle_dict():
    tools = RecHarnessMcpTools.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    result = tools.assist(
        user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
        top_k=1,
    )

    assert result["recommended"][0]["product"]["category"] == "backpack"
    assert result["recommended"][0]["violations"] == []
    assert result["trace_id"].startswith("assist_")


def test_mcp_tools_verify_recommendation_returns_report_dict():
    tools = RecHarnessMcpTools.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    result = tools.verify_recommendation(
        user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
        agent_answer="I recommend RainGuard Metro Pack 24L. It costs 1599 RMB.",
    )

    assert result["status"] == "fail"
    assert result["violations"][0]["constraint"]["field"] == "price.amount"
