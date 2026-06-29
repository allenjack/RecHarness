"""Optional OpenAI Agents SDK demo for RecHarness tools."""

from __future__ import annotations

from recharness import AgentHarnessRouter, AssistRequest, VerifyRequest

try:
    from agents import Agent, Runner, function_tool
except ImportError:
    Agent = Runner = function_tool = None

router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")


def _tool(fn):
    if function_tool is None:
        return fn
    return function_tool(fn)


@_tool
def recharness_list_catalogs() -> dict:
    return router.list_catalogs()


@_tool
def recharness_assist(user_query: str, domain: str, top_k: int = 3) -> dict:
    response = router.assist(
        AssistRequest(user_query=user_query, domain=domain, top_k=top_k)
    )
    return response.model_dump(mode="json")


@_tool
def recharness_verify_recommendation(
    user_query: str,
    domain: str,
    agent_answer: str,
) -> dict:
    response = router.verify(
        VerifyRequest(
            user_query=user_query,
            domain=domain,
            agent_answer=agent_answer,
        )
    )
    return response.model_dump(mode="json")


AGENT_INSTRUCTIONS = """
You are a shopping recommendation assistant using RecHarness.
1. Always call recharness_list_catalogs first.
2. Pick the explicit domain.
3. Call recharness_assist before recommending.
4. Draft an answer using only the returned bundle.
5. Call recharness_verify_recommendation before final answer.
6. Repair or qualify the answer if verification returns warning or fail.
"""


def main() -> None:
    if Agent is None or Runner is None or function_tool is None:
        print(
            "OpenAI Agents SDK is not installed. Install it according to the "
            "official documentation before running this optional demo."
        )
        return
    agent = Agent(
        name="RecHarness recommendation agent",
        instructions=AGENT_INSTRUCTIONS,
        tools=[
            recharness_list_catalogs,
            recharness_assist,
            recharness_verify_recommendation,
        ],
    )
    result = Runner.run_sync(
        agent,
        "想找1000元以内，适合通勤，有降噪的蓝牙耳机",
    )
    print(result.final_output)


if __name__ == "__main__":
    main()
