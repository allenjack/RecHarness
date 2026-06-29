"""Deterministic tool-calling agent demo using plain RecHarness callables."""

from __future__ import annotations

from typing import Any

from recharness import AgentHarnessRouter
from recharness.integrations import make_recharness_tool_functions

DEFAULT_QUERY = "想找1000元以内，适合通勤，有降噪的蓝牙耳机"
CATALOG_CONFIG_PATH = "examples/mcp/catalogs.json"


def choose_domain(catalogs: dict[str, Any], user_query: str) -> str:
    query = user_query.lower()
    available = {item["domain"] for item in catalogs.get("catalogs", [])}
    headphone_terms = [
        "headphones",
        "earphones",
        "earbuds",
        "tws",
        "usb-c",
        "耳机",
        "耳塞",
        "入耳式",
        "真无线",
        "蓝牙",
        "降噪",
    ]
    backpack_terms = ["backpack", "bag", "背包", "双肩包"]

    if any(term in query or term in user_query for term in headphone_terms):
        if "headphones" in available:
            return "headphones"
    if any(term in query or term in user_query for term in backpack_terms):
        if "backpacks" in available:
            return "backpacks"

    default = catalogs.get("default_catalog")
    if default:
        return str(default)
    if available:
        return sorted(available)[0]
    raise ValueError("No catalogs are configured.")


def draft_answer_from_assist_response(assist_response: dict[str, Any]) -> str:
    bundle = assist_response.get("bundle")
    recommended = bundle.get("recommended", []) if isinstance(bundle, dict) else []
    if not recommended:
        return "未找到通过本地目录核验的推荐。"

    lines = ["我建议优先考虑以下推荐："]
    for candidate in recommended[:3]:
        product = candidate.get("product", {})
        title = product.get("title", "未命名商品")
        price = _price_text(product.get("price"))
        facts = _safe_facts(product.get("category", ""), product.get("attributes", {}))
        fact_text = f"，本地目录标注：{'; '.join(facts)}" if facts else ""
        lines.append(f"- {title}{price}{fact_text}")
    return "\n".join(lines)


def repair_or_qualify_answer(answer: str, verify_response: dict[str, Any]) -> str:
    if verify_response.get("status") == "pass":
        return answer

    report = verify_response.get("report") or {}
    repaired = answer
    for issue in report.get("claim_issues", []):
        if issue.get("claim_type") == "noise_cancellation":
            repaired = repaired.replace("，有主动降噪", "")
            repaired = repaired.replace("主动降噪", "目录标注的降噪能力")
        if issue.get("claim_type") == "battery_life":
            repaired = repaired.replace("，续航30小时", "")

    caveats = ["已根据本地目录核验并移除或弱化未通过核验的声明。"]
    if any(violation.get("severity") == "hard" for violation in report.get("violations", [])):
        caveats.append("注意：部分推荐可能不满足硬性约束，请优先查看约束通过的候选。")
    return f"{repaired}\n{' '.join(caveats)}"


def run_agent_loop(user_query: str) -> dict[str, Any]:
    router = AgentHarnessRouter.from_config_file(CATALOG_CONFIG_PATH)
    tools = make_recharness_tool_functions(router)

    catalogs = tools["recharness_list_catalogs"]()
    domain = choose_domain(catalogs, user_query)
    assist = tools["recharness_assist"](user_query=user_query, domain=domain, top_k=3)
    draft = draft_answer_from_assist_response(assist)
    verify = tools["recharness_verify_recommendation"](
        user_query=user_query,
        domain=domain,
        agent_answer=draft,
    )
    final_answer = repair_or_qualify_answer(draft, verify)
    bundle = assist.get("bundle") or {}
    report = verify.get("report") or {}
    return {
        "user_query": user_query,
        "selected_domain": domain,
        "assist_status": assist.get("status"),
        "verify_status": verify.get("status"),
        "recommended_product_ids": _recommended_product_ids(bundle),
        "recommended_titles": _recommended_titles(bundle),
        "final_answer": final_answer,
        "warnings": list(assist.get("warnings", [])) + list(verify.get("warnings", [])),
        "claim_issues": report.get("claim_issues", []),
        "violations": report.get("violations", []),
        "warnings_count": len(assist.get("warnings", [])) + len(verify.get("warnings", [])),
        "claim_issue_count": len(report.get("claim_issues", [])),
        "violation_count": len(report.get("violations", [])),
    }


def run_demo(user_query: str | None = None) -> str:
    return str(run_agent_loop(user_query or DEFAULT_QUERY)["final_answer"])


def _recommended_product_ids(bundle: dict[str, Any]) -> list[str]:
    recommended = bundle.get("recommended", [])
    product_ids: list[str] = []
    for candidate in recommended:
        product = candidate.get("product", {})
        product_id = product.get("product_id")
        if product_id:
            product_ids.append(str(product_id))
    return product_ids


def _recommended_titles(bundle: dict[str, Any]) -> list[str]:
    recommended = bundle.get("recommended", [])
    titles: list[str] = []
    for candidate in recommended:
        product = candidate.get("product", {})
        title = product.get("title")
        if title:
            titles.append(str(title))
    return titles


def _price_text(price: dict[str, Any] | None) -> str:
    if not price:
        return ""
    amount = price.get("amount")
    currency = price.get("currency")
    if amount is None or currency is None:
        return ""
    return f"，售价{amount:g} {currency}"


def _safe_facts(category: str, attributes: dict[str, Any]) -> list[str]:
    if category == "headphones":
        return _attribute_facts(
            attributes,
            [
                ("connection", "连接"),
                ("battery_life_hours", "续航小时"),
                ("latency_ms", "延迟ms"),
                ("water_resistance", "防护"),
                ("noise_cancellation", "目录降噪标记"),
            ],
        )[:2]
    if category == "backpack":
        return _attribute_facts(
            attributes,
            [
                ("laptop_size_inches", "电脑尺寸"),
                ("weight_kg", "重量kg"),
                ("capacity_liters", "容量L"),
                ("water_resistance", "防水"),
            ],
        )[:2]
    return []


def _attribute_facts(attributes: dict[str, Any], fields: list[tuple[str, str]]) -> list[str]:
    facts: list[str] = []
    for key, label in fields:
        value = attributes.get(key)
        if value is not None and value != "":
            facts.append(f"{label}: {value}")
    return facts


def main() -> None:
    print(run_demo())


if __name__ == "__main__":
    main()
