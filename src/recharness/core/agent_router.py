"""Agent-facing multi-catalog routing layer."""

from __future__ import annotations

from pathlib import Path

from recharness.catalog import (
    CatalogLoadError,
    MultiCatalogConfig,
    load_multi_catalog_config,
)
from recharness.core.harness import RecHarness
from recharness.preference import RuleBasedPreferenceParser
from recharness.schema.tools import (
    AssistRequest,
    AssistResponse,
    ParseRequest,
    ParseResponse,
    VerifyRequest,
    VerifyResponse,
)


class AgentHarnessRouter:
    """Route agent-facing requests across configured product catalogs."""

    def __init__(
        self,
        catalog_config: MultiCatalogConfig,
        trace_path: str | Path | None = None,
    ) -> None:
        self.catalog_config = catalog_config
        self.trace_path = trace_path
        self._parser = RuleBasedPreferenceParser()
        self._harness_cache: dict[str, RecHarness] = {}

    @classmethod
    def from_config_file(
        cls,
        config_path: str | Path,
        trace_path: str | Path | None = None,
    ) -> AgentHarnessRouter:
        return cls(load_multi_catalog_config(config_path), trace_path=trace_path)

    def parse(self, request: ParseRequest) -> ParseResponse:
        route = self._resolve_route(request.domain, request.user_query)
        if route.error is not None:
            return ParseResponse(status="error", domain=request.domain, errors=[route.error])
        try:
            harness = self._harness_for(route.domain)
            return ParseResponse(
                status="ok",
                domain=route.domain,
                user_need=harness.parser.parse(request.user_query),
            )
        except Exception as exc:
            return ParseResponse(status="error", domain=route.domain, errors=[str(exc)])

    def assist(self, request: AssistRequest) -> AssistResponse:
        route = self._resolve_route(request.domain, request.user_query)
        if route.error is not None:
            return AssistResponse(status="error", domain=request.domain, errors=[route.error])
        try:
            harness = self._harness_for(route.domain, variant=request.variant)
            bundle = harness.assist(request.user_query, top_k=request.top_k)
            if not request.include_rejected:
                bundle = bundle.model_copy(update={"rejected": []})
            warnings = []
            if bundle.constraint_report.status != "pass":
                warnings.append(
                    bundle.constraint_report.summary or "Constraint diagnostics present"
                )
            return AssistResponse(
                status="ok",
                domain=route.domain,
                bundle=bundle,
                warnings=warnings,
            )
        except Exception as exc:
            return AssistResponse(status="error", domain=route.domain, errors=[str(exc)])

    def verify(self, request: VerifyRequest) -> VerifyResponse:
        route = self._resolve_route(request.domain, request.user_query)
        if route.error is not None:
            return VerifyResponse(status="error", domain=request.domain, errors=[route.error])
        try:
            harness = self._harness_for(route.domain)
            report = harness.verify_agent_recommendation(
                request.user_query,
                request.agent_answer,
            )
            return VerifyResponse(status=report.status, domain=route.domain, report=report)
        except Exception as exc:
            return VerifyResponse(status="error", domain=route.domain, errors=[str(exc)])

    def list_catalogs(self) -> dict:
        return {
            "catalogs": [
                {
                    "domain": domain,
                    "category": config.category,
                    "description": config.description,
                }
                for domain, config in sorted(self.catalog_config.catalogs.items())
            ],
            "default_catalog": self.catalog_config.default_catalog,
        }

    def _harness_for(self, domain: str, variant: str = "full") -> RecHarness:
        if variant != "full":
            return self._build_harness(domain, variant=variant)
        cached = self._harness_cache.get(domain)
        if cached is None:
            cached = self._build_harness(domain, variant=variant)
            self._harness_cache[domain] = cached
        return cached

    def _build_harness(self, domain: str, variant: str = "full") -> RecHarness:
        config = self.catalog_config.catalogs[domain]
        try:
            return RecHarness.from_jsonl_catalog(
                config.path,
                variant=variant,
                trace_path=self.trace_path,
            )
        except CatalogLoadError as exc:
            raise ValueError(str(exc)) from exc

    def _resolve_route(self, explicit_domain: str | None, query: str) -> _RouteResult:
        if explicit_domain:
            if explicit_domain not in self.catalog_config.catalogs:
                return _RouteResult(
                    domain=explicit_domain,
                    error=f"Unknown domain: {explicit_domain}",
                )
            return _RouteResult(domain=explicit_domain)

        need = self._parser.parse(query)
        if need.category is not None:
            for domain, config in self.catalog_config.catalogs.items():
                if config.category == need.category:
                    return _RouteResult(domain=domain)

        if self.catalog_config.default_catalog is not None:
            return _RouteResult(domain=self.catalog_config.default_catalog)

        return _RouteResult(domain=None, error="No catalog route could be resolved")


class _RouteResult:
    def __init__(self, domain: str | None, error: str | None = None) -> None:
        self.domain = domain
        self.error = error
