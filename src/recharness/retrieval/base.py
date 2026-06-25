"""Shared retrieval types."""

from __future__ import annotations

from pydantic import Field

from recharness.schema import ProductItem, RecHarnessModel


class ScoredProduct(RecHarnessModel):
    product: ProductItem
    score: float = Field(ge=0, le=1)
    matched_terms: list[str] = Field(default_factory=list)
