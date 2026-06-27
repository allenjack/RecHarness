"""Constraint-aware product scoring."""

from __future__ import annotations

from collections.abc import Sequence

from recharness.retrieval.base import ScoredProduct
from recharness.schema import ProductItem, UserNeed
from recharness.verification import ConstraintVerifier


class AttributeFilterRetriever:
    """Score every product by parsed hard-constraint compatibility."""

    def __init__(self, verifier: ConstraintVerifier | None = None) -> None:
        self.verifier = verifier or ConstraintVerifier()

    def retrieve(
        self,
        need: UserNeed,
        catalog: Sequence[ProductItem],
        top_k: int = 10,
    ) -> list[ScoredProduct]:
        results: list[ScoredProduct] = []
        for product in catalog:
            report = self.verifier.verify_product(product, need.hard_constraints)
            score = _constraint_score(report.checks)
            results.append(ScoredProduct(product=product, score=score, matched_terms=[]))
        return sorted(
            results,
            key=lambda result: (-result.score, result.product.product_id),
        )[:top_k]


def _constraint_score(checks) -> float:
    if not checks:
        return 1.0
    satisfied = sum(1 for check in checks if check.satisfied)
    return round(0.2 + 0.8 * (satisfied / len(checks)), 6)
