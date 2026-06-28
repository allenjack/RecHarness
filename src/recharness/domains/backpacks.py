"""Backpack domain adapter."""

from __future__ import annotations

from recharness.schema import ClaimIssue, ProductItem, UserNeed


class BackpacksAdapter:
    category = "backpack"

    def enrich_user_need(self, need: UserNeed, query: str) -> UserNeed:
        return need

    def verify_claims(self, product: ProductItem, text: str) -> list[ClaimIssue]:
        return []
