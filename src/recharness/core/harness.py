"""SDK-level RecHarness orchestration."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from recharness.catalog import JsonlCatalog
from recharness.preference import RuleBasedPreferenceParser
from recharness.ranking import SimpleRanker
from recharness.retrieval import HybridRetriever
from recharness.schema import RecommendationBundle
from recharness.tracing import JsonlTraceLogger
from recharness.verification import ConstraintVerifier, RecommendationVerifier


class RecHarness:
    """Deterministic recommendation harness for local product catalogs."""

    def __init__(
        self,
        catalog: JsonlCatalog,
        parser: RuleBasedPreferenceParser | None = None,
        retriever: HybridRetriever | None = None,
        ranker: SimpleRanker | None = None,
        verifier: ConstraintVerifier | None = None,
        recommendation_verifier: RecommendationVerifier | None = None,
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
        self.trace_logger = trace_logger

    @classmethod
    def from_jsonl_catalog(
        cls,
        path: str | Path,
        trace_path: str | Path | None = None,
    ) -> RecHarness:
        trace_logger = JsonlTraceLogger(trace_path) if trace_path is not None else None
        return cls(catalog=JsonlCatalog.load(path), trace_logger=trace_logger)

    def assist(self, user_query: str, top_k: int = 5) -> RecommendationBundle:
        trace_id = f"assist_{uuid4().hex}"
        need = self.parser.parse(user_query)
        self._trace(trace_id, 1, "parse_preferences", need.model_dump(mode="json"))
        retrieved = self.retriever.retrieve(need, self.catalog, top_k=max(top_k * 3, top_k))
        self._trace(
            trace_id,
            2,
            "retrieve",
            {
                "retrieved_count": len(retrieved),
                "product_ids": [item.product.product_id for item in retrieved],
            },
        )
        ranked = self.ranker.rank(need, retrieved, top_k=top_k)
        self._trace(
            trace_id,
            3,
            "rank",
            {
                "ranked_count": len(ranked),
                "product_ids": [candidate.product.product_id for candidate in ranked],
            },
        )

        bundle = RecommendationBundle(
            user_need=need,
            candidates=ranked,
            recommended=ranked,
            rejected=[],
            comparison_axes=_comparison_axes(need),
            constraint_report=None,
            clarification_questions=[],
            summary_for_agent=_summary_for_agent(ranked),
            trace_id=trace_id,
        )
        self._trace(
            trace_id,
            4,
            "bundle",
            {"recommended": [candidate.product.product_id for candidate in bundle.recommended]},
        )
        return bundle

    def verify_agent_recommendation(self, user_query: str, agent_answer: str):
        need = self.parser.parse(user_query)
        return self.recommendation_verifier.verify(need, agent_answer, self.catalog)

    def _trace(self, trace_id: str, step: int, event_type: str, payload: dict) -> None:
        if self.trace_logger is not None:
            self.trace_logger.log(
                trace_id=trace_id,
                step=step,
                event_type=event_type,
                payload=payload,
            )


def _comparison_axes(need) -> list[str]:
    axes = [constraint.field for constraint in need.hard_constraints]
    axes.extend(preference.field for preference in need.negative_preferences)
    return axes


def _summary_for_agent(ranked) -> str:
    if not ranked:
        return "No catalog products matched the parsed hard constraints."

    names = ", ".join(candidate.product.title for candidate in ranked[:3])
    first = ranked[0].product.title
    return f"Recommend {first} as the safest choice. Other viable options: {names}."
