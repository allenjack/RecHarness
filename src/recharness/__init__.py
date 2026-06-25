"""Public API for the RecHarness foundation package."""

from recharness.catalog import (
    CatalogIssue,
    CatalogLoadError,
    CatalogStats,
    CatalogValidationReport,
    JsonlCatalog,
)
from recharness.preference import RuleBasedPreferenceParser
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
from recharness.verification import ConstraintVerifier

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
    "RuleBasedPreferenceParser",
    "TraceEvent",
    "UserNeed",
    "VerificationReport",
    "Violation",
    "ConstraintVerifier",
]
