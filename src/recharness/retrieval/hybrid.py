"""Hybrid retrieval that filters constraints and preserves keyword ranking."""

from __future__ import annotations

from collections.abc import Sequence

from recharness.retrieval.attribute_filter import AttributeFilterRetriever
from recharness.retrieval.base import ScoredProduct
from recharness.retrieval.keyword import KeywordRetriever
from recharness.schema import ProductItem, UserNeed


class HybridRetriever:
    """Combine keyword recall with hard-constraint filtering."""

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
        allowed = {
            result.product.product_id
            for result in self.attribute_filter.retrieve(need, catalog, top_k=len(catalog))
        }
        keyword_results = self.keyword.retrieve(need, catalog, top_k=len(catalog))
        filtered = [result for result in keyword_results if result.product.product_id in allowed]
        return filtered[:top_k]
