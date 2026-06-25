"""Public API for the RecHarness foundation package."""

from recharness.catalog import (
    CatalogIssue,
    CatalogLoadError,
    CatalogStats,
    CatalogValidationReport,
    JsonlCatalog,
)
from recharness.schema import (
    Constraint,
    ConstraintCheck,
    Evidence,
    Money,
    Preference,
    ProductItem,
    RecommendationBundle,
    RecommendationCandidate,
    TraceEvent,
    UserNeed,
    VerificationReport,
    Violation,
)

__all__ = [
    "CatalogIssue",
    "CatalogLoadError",
    "CatalogStats",
    "CatalogValidationReport",
    "Constraint",
    "ConstraintCheck",
    "Evidence",
    "JsonlCatalog",
    "Money",
    "Preference",
    "ProductItem",
    "RecommendationBundle",
    "RecommendationCandidate",
    "TraceEvent",
    "UserNeed",
    "VerificationReport",
    "Violation",
]
