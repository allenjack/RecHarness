"""SDK-level RecHarness orchestration."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from recharness.catalog import JsonlCatalog
from recharness.preference import RuleBasedPreferenceParser
from recharness.ranking import SimpleRanker
from recharness.retrieval import HybridRetriever
from recharness.schema import RecommendationBundle
from recharness.verification import ConstraintVerifier


class RecHarness:
    """Deterministic recommendation harness for local product catalogs."""

    def __init__(
        self,
        catalog: JsonlCatalog,
        parser: RuleBasedPreferenceParser | None = None,
        retriever: HybridRetriever | None = None,
        ranker: SimpleRanker | None = None,
        verifier: ConstraintVerifier | None = None,
    ) -> None:
        self.catalog = catalog
        self.parser = parser or RuleBasedPreferenceParser()
        self.verifier = verifier or ConstraintVerifier()
        self.retriever = retriever or HybridRetriever()
        self.ranker = ranker or SimpleRanker(verifier=self.verifier)

    @classmethod
    def from_jsonl_catalog(cls, path: str | Path) -> "RecHarness":
        return cls(catalog=JsonlCatalog.load(path))

    def assist(self, user_query: str, top_k: int = 5) -> RecommendationBundle:
        need = self.parser.parse(user_query)
        retrieved = self.retriever.retrieve(need, self.catalog, top_k=max(top_k * 3, top_k))
        ranked = self.ranker.rank(need, retrieved, top_k=top_k)

        return RecommendationBundle(
            user_need=need,
            candidates=ranked,
            recommended=ranked,
            rejected=[],
            comparison_axes=_comparison_axes(need),
            constraint_report=None,
            clarification_questions=[],
            summary_for_agent=_summary_for_agent(ranked),
            trace_id=f"assist_{uuid4().hex}",
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
