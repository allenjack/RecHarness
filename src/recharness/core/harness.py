"""SDK-level RecHarness orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from recharness.bundle import BundleBuilder
from recharness.catalog import JsonlCatalog
from recharness.core.config import HarnessVariant
from recharness.preference import RuleBasedPreferenceParser
from recharness.ranking import SimpleRanker
from recharness.retrieval import AttributeFilterRetriever, HybridRetriever, KeywordRetriever
from recharness.schema import RecommendationBundle
from recharness.tracing import JsonlTraceLogger
from recharness.verification import ConstraintVerifier, RecommendationVerifier


class RecHarness:
    """Deterministic recommendation harness for local product catalogs."""

    def __init__(
        self,
        catalog: JsonlCatalog,
        parser: RuleBasedPreferenceParser | None = None,
        retriever: Any | None = None,
        ranker: SimpleRanker | None = None,
        verifier: ConstraintVerifier | None = None,
        recommendation_verifier: RecommendationVerifier | None = None,
        bundle_builder: BundleBuilder | None = None,
        trace_logger: JsonlTraceLogger | None = None,
    ) -> None:
        self.catalog = catalog
        self.parser = parser or RuleBasedPreferenceParser()
        self.verifier = verifier or ConstraintVerifier()
        self.recommendation_verifier = recommendation_verifier or RecommendationVerifier(
            constraint_verifier=self.verifier
        )
        self.retriever = retriever or HybridRetriever()
        self.ranker = ranker or SimpleRanker(verifier=self.verifier)
        self.bundle_builder = bundle_builder or BundleBuilder()
        self.trace_logger = trace_logger

    @classmethod
    def from_jsonl_catalog(
        cls,
        path: str | Path,
        variant: str | Path = "full",
        trace_path: str | Path | None = None,
    ) -> RecHarness:
        variant, trace_path = _normalize_variant_and_trace_path(variant, trace_path)
        trace_logger = JsonlTraceLogger(trace_path) if trace_path is not None else None
        return cls(
            catalog=JsonlCatalog.load(path),
            retriever=_retriever_for_variant(variant),
            trace_logger=trace_logger,
        )

    def assist(self, user_query: str, top_k: int = 5) -> RecommendationBundle:
        trace_id = f"assist_{uuid4().hex}"
        need = self.parser.parse(user_query)
        self._trace(trace_id, 1, "parse_preferences", need.model_dump(mode="json"))
        retrieved = self.retriever.retrieve(need, self.catalog, top_k=len(self.catalog))
        self._trace(
            trace_id,
            2,
            "retrieve",
            {
                "retrieved_count": len(retrieved),
                "product_ids": [item.product.product_id for item in retrieved],
            },
        )
        ranked = self.ranker.rank(need, retrieved, top_k=len(retrieved))
        self._trace(
            trace_id,
            3,
            "rank",
            {
                "ranked_count": len(ranked),
                "product_ids": [candidate.product.product_id for candidate in ranked],
            },
        )

        bundle = self.bundle_builder.build(need, ranked, top_k=top_k, trace_id=trace_id)
        self._trace(
            trace_id,
            4,
            "bundle",
            {
                "recommended": [candidate.product.product_id for candidate in bundle.recommended],
                "rejected": [candidate.product.product_id for candidate in bundle.rejected],
                "constraint_report": (
                    bundle.constraint_report.model_dump(mode="json")
                    if bundle.constraint_report is not None
                    else None
                ),
            },
        )
        return bundle

    def verify_agent_recommendation(self, user_query: str, agent_answer: str):
        trace_id = f"verify_{uuid4().hex}"
        need = self.parser.parse(user_query)
        self._trace(trace_id, 1, "parse_preferences", need.model_dump(mode="json"))
        report = self.recommendation_verifier.verify(need, agent_answer, self.catalog)
        self._trace(
            trace_id,
            2,
            "resolve_mentions",
            {
                "mentioned_products": report.mentioned_products,
                "resolved_product_ids": [
                    product.product_id for product in report.resolved_products
                ],
                "unresolved_mentions": report.unresolved_mentions,
            },
        )
        self._trace(
            trace_id,
            3,
            "verify_constraints",
            {
                "violations": [
                    violation.model_dump(mode="json") for violation in report.violations
                ],
            },
        )
        self._trace(
            trace_id,
            4,
            "claim_check",
            {
                "claim_issues": [
                    issue.model_dump(mode="json") for issue in report.claim_issues
                ],
            },
        )
        self._trace(
            trace_id,
            5,
            "verify_agent_answer",
            {
                "status": report.status,
                "summary": report.summary,
                "product_grounded": report.product_grounded,
            },
        )
        return report

    def _trace(self, trace_id: str, step: int, event_type: str, payload: dict) -> None:
        if self.trace_logger is not None:
            self.trace_logger.log(
                trace_id=trace_id,
                step=step,
                event_type=event_type,
                payload=payload,
            )


def _normalize_variant_and_trace_path(
    variant: str | Path,
    trace_path: str | Path | None,
) -> tuple[str, str | Path | None]:
    if isinstance(variant, Path):
        return "full", variant if trace_path is None else trace_path
    if trace_path is None and ("/" in variant or variant.endswith(".jsonl")):
        return "full", variant
    return variant, trace_path


def _retriever_for_variant(variant: str) -> Any:
    parsed = HarnessVariant.parse(variant)
    if parsed == HarnessVariant.FULL:
        return HybridRetriever()
    if parsed == HarnessVariant.KEYWORD_ONLY:
        return KeywordRetriever()
    if parsed == HarnessVariant.CONSTRAINT_ONLY:
        return AttributeFilterRetriever()
    raise ValueError(f"Unknown harness variant '{variant}'")
