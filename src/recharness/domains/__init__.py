"""Domain adapter registry."""

from recharness.domains.base import DomainAdapter
from recharness.domains.registry import get_domain_adapter

__all__ = ["DomainAdapter", "get_domain_adapter"]
