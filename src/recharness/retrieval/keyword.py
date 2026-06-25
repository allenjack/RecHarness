"""Simple keyword retrieval over product text fields."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

from recharness.retrieval.base import ScoredProduct
from recharness.schema import ProductItem, UserNeed


class KeywordRetriever:
    """Rank products by deterministic keyword overlap."""

    def retrieve(
        self,
        need: UserNeed,
        catalog: Sequence[ProductItem],
        top_k: int = 10,
    ) -> list[ScoredProduct]:
        terms = _need_terms(need)
        results: list[ScoredProduct] = []

        for product in catalog:
            text = _product_text(product)
            matched = [term for term in terms if term in text]
            if matched:
                score = min(1.0, len(matched) / max(len(terms), 1))
                results.append(ScoredProduct(product=product, score=score, matched_terms=matched))

        return sorted(
            results,
            key=lambda result: (-result.score, result.product.product_id),
        )[:top_k]


def _need_terms(need: UserNeed) -> list[str]:
    raw_terms = _tokens(need.raw_query)
    terms = set(raw_terms)
    if need.category:
        terms.add(need.category)
    terms.update(need.scenario)

    normalized: set[str] = set()
    for term in terms:
        if term.startswith("commut"):
            normalized.add("commute")
        else:
            normalized.add(term)
    return sorted(term for term in normalized if len(term) >= 3 and not term.isdigit())


def _product_text(product: ProductItem) -> str:
    parts: list[str] = [
        product.product_id,
        product.title,
        product.category,
        product.brand or "",
        product.description or "",
        product.review_summary or "",
        " ".join(product.tags),
    ]
    parts.extend(_flatten_values(product.attributes))
    text = " ".join(parts).lower()
    if "commuter" in text or "commuting" in text:
        text = f"{text} commute"
    return text


def _flatten_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_flatten_values(item))
        return values
    if isinstance(value, (list, tuple, set)):
        values = []
        for item in value:
            values.extend(_flatten_values(item))
        return values
    return [str(value)]


def _tokens(text: str) -> Iterable[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9_]+", text.lower())
