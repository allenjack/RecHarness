"""Optional MCP server integration for RecHarness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from recharness.catalog import CatalogConfig, MultiCatalogConfig
from recharness.core import AgentHarnessRouter
from recharness.schema.tools import AssistRequest, ParseRequest, VerifyRequest


class RecHarnessMcpTools:
    """JSON-serializable tool adapter used by the optional MCP server."""

    def __init__(self, router: AgentHarnessRouter) -> None:
        self.router = router

    @classmethod
    def from_jsonl_catalog(cls, catalog_path: str | Path) -> RecHarnessMcpTools:
        config = MultiCatalogConfig(
            catalogs={"default": CatalogConfig(path=str(catalog_path))},
            default_catalog="default",
        )
        return cls(AgentHarnessRouter(config))

    @classmethod
    def from_config_file(cls, config_path: str | Path) -> RecHarnessMcpTools:
        return cls(AgentHarnessRouter.from_config_file(config_path))

    def list_catalogs(self) -> dict[str, Any]:
        return self.router.list_catalogs()

    def parse_preferences(self, user_query: str, domain: str | None = None) -> dict[str, Any]:
        response = self.router.parse(ParseRequest(user_query=user_query, domain=domain))
        return response.model_dump(mode="json")

    def assist(
        self,
        user_query: str,
        domain: str | None = None,
        top_k: int = 5,
        include_rejected: bool = True,
        variant: str = "full",
    ) -> dict[str, Any]:
        response = self.router.assist(
            AssistRequest(
                user_query=user_query,
                domain=domain,
                top_k=top_k,
                include_rejected=include_rejected,
                variant=variant,
            )
        )
        return response.model_dump(mode="json")

    def verify_recommendation(
        self,
        user_query: str,
        agent_answer: str,
        domain: str | None = None,
    ) -> dict[str, Any]:
        response = self.router.verify(
            VerifyRequest(
                user_query=user_query,
                agent_answer=agent_answer,
                domain=domain,
            )
        )
        return response.model_dump(mode="json")


def create_mcp_server(
    catalog_path: str | Path | None = None,
    config_path: str | Path | None = None,
):
    """Create a FastMCP server when the optional `mcp` package is installed."""

    if (catalog_path is None) == (config_path is None):
        raise RuntimeError("Provide exactly one of catalog_path or config_path.")

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "Install RecHarness with the 'mcp' extra to use the MCP server."
        ) from exc

    tools = (
        RecHarnessMcpTools.from_config_file(config_path)
        if config_path is not None
        else RecHarnessMcpTools.from_jsonl_catalog(catalog_path)
    )
    server = FastMCP("RecHarness")

    @server.tool()
    def recharness_list_catalogs() -> dict[str, Any]:
        """List configured RecHarness catalogs."""

        return tools.list_catalogs()

    @server.tool()
    def recharness_parse_preferences(
        user_query: str,
        domain: str | None = None,
    ) -> dict[str, Any]:
        """Parse a shopping query into structured preferences and constraints."""

        return tools.parse_preferences(user_query=user_query, domain=domain)

    @server.tool()
    def recharness_assist(
        user_query: str,
        domain: str | None = None,
        top_k: int = 5,
        include_rejected: bool = True,
        variant: str = "full",
    ) -> dict[str, Any]:
        """Return a grounded recommendation bundle for a shopping query."""

        return tools.assist(
            user_query=user_query,
            domain=domain,
            top_k=top_k,
            include_rejected=include_rejected,
            variant=variant,
        )

    @server.tool()
    def recharness_verify_recommendation(
        user_query: str,
        agent_answer: str,
        domain: str | None = None,
    ) -> dict[str, Any]:
        """Verify whether an agent answer satisfies parsed user constraints."""

        return tools.verify_recommendation(
            user_query=user_query,
            agent_answer=agent_answer,
            domain=domain,
        )

    return server
