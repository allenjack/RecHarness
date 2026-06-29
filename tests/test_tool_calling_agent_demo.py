from examples.integrations.tool_calling_agent_demo import (
    choose_domain,
    run_agent_loop,
    run_demo,
)


def test_tool_calling_agent_demo_selects_domain_deterministically():
    catalogs = {
        "default_catalog": "backpacks",
        "catalogs": [
            {"domain": "backpacks"},
            {"domain": "headphones"},
        ],
    }

    assert choose_domain(catalogs, "想找有降噪的蓝牙耳机") == "headphones"
    assert choose_domain(catalogs, "Need low-latency gaming headphones") == "headphones"
    assert choose_domain(catalogs, "Find a commuting backpack") == "backpacks"
    assert choose_domain(catalogs, "Find something affordable") == "backpacks"


def test_tool_calling_agent_demo_runs_without_external_agent_frameworks():
    answer = run_demo("想找1000元以内，适合通勤，有降噪的蓝牙耳机")

    assert "推荐" in answer or "我建议" in answer
    assert "主动降噪" not in answer or "已根据本地目录核验" in answer
    assert "部分推荐可能不满足硬性约束" not in answer


def test_tool_calling_agent_loop_returns_structured_result():
    result = run_agent_loop("想找1000元以内，适合通勤，有降噪的蓝牙耳机")

    assert result["user_query"] == "想找1000元以内，适合通勤，有降噪的蓝牙耳机"
    assert result["selected_domain"] == "headphones"
    assert result["assist_status"] in {"ok", "warning"}
    assert result["verify_status"] in {"pass", "warning", "fail"}
    assert result["recommended_product_ids"]
    assert result["final_answer"] == run_demo("想找1000元以内，适合通勤，有降噪的蓝牙耳机")
    assert isinstance(result["warnings"], list)
    assert isinstance(result["claim_issues"], list)
    assert isinstance(result["violations"], list)
