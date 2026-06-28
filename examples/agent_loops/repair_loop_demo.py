from recharness import AgentHarnessRouter, VerifyRequest


def repair_answer(draft_answer: str, report) -> str:
    repaired = draft_answer
    if report is None:
        return repaired
    for issue in report.claim_issues:
        if issue.claim_type == "noise_cancellation":
            repaired = repaired.replace("，有主动降噪", "")
        if issue.claim_type == "battery_life":
            repaired = repaired.replace("，续航30小时", "")
    if report.repair_suggestions:
        repaired = f"{repaired}（已移除未通过核验的声明。）"
    return repaired


def main() -> None:
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")
    user_query = "想找1000元以内，适合通勤，有降噪的蓝牙耳机"
    draft_answer = "我推荐 SonicLite AirBuds，售价699元，有主动降噪，续航30小时。"

    verify = router.verify(
        VerifyRequest(
            user_query=user_query,
            domain="headphones",
            agent_answer=draft_answer,
        )
    )
    if verify.status != "pass":
        draft_answer = repair_answer(draft_answer, verify.report)

    print(draft_answer)


if __name__ == "__main__":
    main()
