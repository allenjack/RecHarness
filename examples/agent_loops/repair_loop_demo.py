from recharness import AgentHarnessRouter, VerifyRequest
from recharness.core.answer_repair import repair_or_qualify_answer


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
        draft_answer = repair_or_qualify_answer(draft_answer, verify)

    print(draft_answer)


if __name__ == "__main__":
    main()
