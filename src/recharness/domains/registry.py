"""Domain adapter registry."""

from __future__ import annotations

from recharness.domains.backpacks import BackpacksAdapter
from recharness.domains.base import DomainAdapter
from recharness.domains.headphones import HeadphonesAdapter

_ADAPTERS: dict[str, DomainAdapter] = {
    "backpack": BackpacksAdapter(),
    "headphones": HeadphonesAdapter(),
}


def get_domain_adapter(category: str | None) -> DomainAdapter | None:
    if category is None:
        return None
    return _ADAPTERS.get(category)
