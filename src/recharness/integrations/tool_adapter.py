"""Framework-neutral tool-callable functions for RecHarness."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from recharness.core import AgentHarnessRouter
from recharness.schema.tools import AssistRequest, VerifyRequest


def make_recharness_tool_functions(
    router: AgentHarnessRouter,
) -> dict[str, Callable[..., dict[str, Any]]]:
    """Return plain Python callables suitable for wrapping by agent frameworks."""

    def recharness_list_catalogs() -> dict[str, Any]:
        try:
            return router.list_catalogs()
        except Exception as exc:
            return _error_dict(exc)

    def recharness_assist(
        user_query: str,
        domain: str,
        top_k: int = 3,
    ) -> dict[str, Any]:
        try:
            response = router.assist(
                AssistRequest(user_query=user_query, domain=domain, top_k=top_k)
            )
            return response.model_dump(mode="json")
        except Exception as exc:
            return _error_dict(exc)

    def recharness_verify_recommendation(
        user_query: str,
        domain: str,
        agent_answer: str,
    ) -> dict[str, Any]:
        try:
            response = router.verify(
                VerifyRequest(
                    user_query=user_query,
                    domain=domain,
                    agent_answer=agent_answer,
                )
            )
            return response.model_dump(mode="json")
        except Exception as exc:
            return _error_dict(exc)

    return {
        "recharness_list_catalogs": recharness_list_catalogs,
        "recharness_assist": recharness_assist,
        "recharness_verify_recommendation": recharness_verify_recommendation,
    }


def _error_dict(exc: Exception) -> dict[str, Any]:
    return {"status": "error", "errors": [str(exc)]}
