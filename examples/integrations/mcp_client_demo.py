"""Deterministic MCP-style client demo using the local router."""

from __future__ import annotations

from typing import Any

from recharness import AgentHarnessRouter, AssistRequest, VerifyRequest

DEFAULT_QUERY = "想找1000元以内，适合通勤，有降噪的蓝牙耳机"


def select_domain(catalogs: dict, user_query: str) -> str:
    query = user_query.lower()
    available = {item["domain"] for item in catalogs.get("catalogs", [])}
    headphone_terms = ["headphones", "earphones", "earbuds", "耳机", "蓝牙", "降噪"]
    if any(term in query or term in user_query for term in headphone_terms):
        if "headphones" in available:
            return "headphones"
    if any(term in query or term in user_query for term in ["backpack", "bag", "背包", "双肩包"]):
        if "backpacks" in available:
            return "backpacks"
    default = catalogs.get("default_catalog")
    if default:
        return str(default)
    if available:
        return sorted(available)[0]
    raise ValueError("No catalogs are configured.")


def draft_answer_from_bundle(bundle) -> str:
    if bundle is None or not bundle.recommended:
        return "未找到通过本地目录核验的推荐。"
    lines = ["我建议优先考虑以下候选："]
    for candidate in bundle.recommended[:3]:
        product = candidate.product
        facts = _safe_facts(product.category, product.attributes)
        price = ""
        if product.price is not None:
            price = f"，售价{product.price.amount:g} {product.price.currency}"
        fact_text = f"，{'; '.join(facts)}" if facts else ""
        lines.append(f"- {product.title}{price}{fact_text}")
    return "\n".join(lines)


def repair_or_qualify_answer(answer: str, report) -> str:
    if report is None or report.status == "pass":
        return answer
    repaired = answer
    for issue in report.claim_issues:
        if issue.claim_type == "noise_cancellation":
            repaired = repaired.replace("，有主动降噪", "")
        if issue.claim_type == "battery_life":
            repaired = repaired.replace("，续航30小时", "")
    caveats = ["已根据本地目录核验并移除或弱化未通过核验的声明。"]
    if any(violation.severity == "hard" for violation in report.violations):
        caveats.append("注意：部分推荐可能不满足硬性约束，请优先查看约束通过的候选。")
    return f"{repaired}\n{' '.join(caveats)}"


def run_demo(user_query: str | None = None) -> str:
    query = user_query or DEFAULT_QUERY
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")
    catalogs = router.list_catalogs()
    domain = select_domain(catalogs, query)
    assist = router.assist(AssistRequest(user_query=query, domain=domain, top_k=3))
    draft = draft_answer_from_bundle(assist.bundle)
    verify = router.verify(
        VerifyRequest(user_query=query, domain=domain, agent_answer=draft)
    )
    return repair_or_qualify_answer(draft, verify.report)


def _safe_facts(category: str, attributes: dict[str, Any]) -> list[str]:
    if category == "headphones":
        return _attribute_facts(
            attributes,
            [
                ("connection", "连接"),
                ("noise_cancellation", "降噪"),
                ("battery_life_hours", "续航小时"),
                ("latency_ms", "延迟ms"),
                ("water_resistance", "防护"),
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
