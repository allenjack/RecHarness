from recharness import AgentHarnessRouter, AssistRequest, VerifyRequest
from recharness.core.answer_repair import repair_or_qualify_answer


def build_simple_answer_from_bundle(bundle) -> str:
    candidate = bundle.recommended[0]
    product = candidate.product
    price = (
        f"{product.price.amount:g} {product.price.currency}"
        if product.price
        else "unknown price"
    )
    return f"我推荐 {product.title}，售价{price}。"


def main() -> None:
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")
    user_query = "想找1000元以内，适合通勤，有降噪的蓝牙耳机"

    assist = router.assist(
        AssistRequest(
            user_query=user_query,
            domain="headphones",
            top_k=3,
        )
    )
    if assist.bundle is None:
        print("; ".join(assist.errors))
        return

    draft_answer = build_simple_answer_from_bundle(assist.bundle)
    verify = router.verify(
        VerifyRequest(
            user_query=user_query,
            domain="headphones",
            agent_answer=draft_answer,
        )
    )

    if verify.status != "pass":
        draft_answer = repair_or_qualify_answer(draft_answer, verify, assist_response=assist)

    print(draft_answer)


if __name__ == "__main__":
    main()
