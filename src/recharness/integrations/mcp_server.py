"""Optional MCP server integration for RecHarness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from recharness.core import RecHarness


class RecHarnessMcpTools:
    """JSON-serializable tool adapter used by the optional MCP server."""

    def __init__(self, harness: RecHarness) -> None:
        self.harness = harness

    @classmethod
    def from_jsonl_catalog(cls, catalog_path: str | Path) -> RecHarnessMcpTools:
        return cls(RecHarness.from_jsonl_catalog(catalog_path))

    def parse_preferences(self, user_query: str) -> dict[str, Any]:
        need = self.harness.parser.parse(user_query)
        return need.model_dump(mode="json")

    def assist(self, user_query: str, top_k: int = 5) -> dict[str, Any]:
        bundle = self.harness.assist(user_query=user_query, top_k=top_k)
        return bundle.model_dump(mode="json")

    def verify_recommendation(self, user_query: str, agent_answer: str) -> dict[str, Any]:
        report = self.harness.verify_agent_recommendation(
            user_query=user_query,
            agent_answer=agent_answer,
        )
        return report.model_dump(mode="json")


def create_mcp_server(catalog_path: str | Path):
    """Create a FastMCP server when the optional `mcp` package is installed."""

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "Install RecHarness with the 'mcp' extra to use the MCP server."
        ) from exc

    tools = RecHarnessMcpTools.from_jsonl_catalog(catalog_path)
    server = FastMCP("RecHarness")

    @server.tool()
    def parse_preferences(user_query: str) -> dict[str, Any]:
        """Parse a shopping query into structured preferences and constraints."""

        return tools.parse_preferences(user_query)

    @server.tool()
    def assist(user_query: str, top_k: int = 5) -> dict[str, Any]:
        """Return a grounded recommendation bundle for a shopping query."""

        return tools.assist(user_query=user_query, top_k=top_k)

    @server.tool()
    def verify_recommendation(user_query: str, agent_answer: str) -> dict[str, Any]:
        """Verify whether an agent answer satisfies parsed user constraints."""

        return tools.verify_recommendation(user_query=user_query, agent_answer=agent_answer)

    return server
