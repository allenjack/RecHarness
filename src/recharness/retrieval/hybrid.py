"""Hybrid retrieval that blends keyword and constraint scores."""

from __future__ import annotations

from collections.abc import Sequence

from recharness.retrieval.attribute_filter import AttributeFilterRetriever
from recharness.retrieval.base import ScoredProduct
from recharness.retrieval.keyword import KeywordRetriever
from recharness.schema import ProductItem, UserNeed


class HybridRetriever:
    """Combine keyword recall with soft constraint scoring."""

    def __init__(
        self,
        keyword: KeywordRetriever | None = None,
        attribute_filter: AttributeFilterRetriever | None = None,
    ) -> None:
        self.keyword = keyword or KeywordRetriever()
        self.attribute_filter = attribute_filter or AttributeFilterRetriever()

    def retrieve(
        self,
        need: UserNeed,
        catalog: Sequence[ProductItem],
        top_k: int = 10,
    ) -> list[ScoredProduct]:
        constraint_results = self.attribute_filter.retrieve(need, catalog, top_k=len(catalog))
        constraint_by_id = {
            result.product.product_id: result.score for result in constraint_results
        }
        keyword_results = self.keyword.retrieve(need, catalog, top_k=len(catalog))
        keyword_by_id = {
            result.product.product_id: result for result in keyword_results
        }

        merged: list[ScoredProduct] = []
        for product in catalog:
            keyword = keyword_by_id.get(product.product_id)
            keyword_score = keyword.score if keyword is not None else 0.0
            constraint_score = constraint_by_id.get(product.product_id, 1.0)
            score = round(0.65 * constraint_score + 0.35 * keyword_score, 6)
            merged.append(
                ScoredProduct(
                    product=product,
                    score=score,
                    matched_terms=keyword.matched_terms if keyword is not None else [],
                )
            )

        return sorted(
            merged,
            key=lambda result: (-result.score, result.product.product_id),
        )[:top_k]
