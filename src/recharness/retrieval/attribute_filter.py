"""Hard-constraint product filtering."""

from __future__ import annotations

from collections.abc import Sequence

from recharness.retrieval.base import ScoredProduct
from recharness.schema import ProductItem, UserNeed
from recharness.verification import ConstraintVerifier


class AttributeFilterRetriever:
    """Return products that satisfy all parsed hard constraints."""

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
            if report.status == "pass":
                results.append(ScoredProduct(product=product, score=1.0, matched_terms=[]))
        return results[:top_k]
