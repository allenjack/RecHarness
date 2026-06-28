"""Domain adapter interface."""

from __future__ import annotations

from typing import Protocol

from recharness.schema import ClaimIssue, ProductItem, UserNeed


class DomainAdapter(Protocol):
    category: str

    def enrich_user_need(self, need: UserNeed, query: str) -> UserNeed:
        ...

    def verify_claims(self, product: ProductItem, text: str) -> list[ClaimIssue]:
        ...
