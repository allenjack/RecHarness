"""Public API for the RecHarness foundation package."""

from recharness.catalog import (
    CatalogIssue,
    CatalogLoadError,
    CatalogStats,
    CatalogValidationReport,
    JsonlCatalog,
)
from recharness.core import RecHarness
from recharness.preference import RuleBasedPreferenceParser
from recharness.ranking import SimpleRanker
from recharness.retrieval import (
    AttributeFilterRetriever,
    HybridRetriever,
    KeywordRetriever,
    ScoredProduct,
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
from recharness.verification import ClaimVerifier, ConstraintVerifier, RecommendationVerifier

__all__ = [
    "CatalogIssue",
    "CatalogLoadError",
    "CatalogStats",
    "CatalogValidationReport",
    "ClaimVerifier",
    "Constraint",
    "ConstraintCheck",
    "AttributeFilterRetriever",
    "Evidence",
    "HybridRetriever",
    "JsonlCatalog",
    "KeywordRetriever",
    "Money",
    "Preference",
    "ProductItem",
    "RecHarness",
    "RecommendationBundle",
    "RecommendationCandidate",
    "RuleBasedPreferenceParser",
    "ScoredProduct",
    "SimpleRanker",
    "TraceEvent",
    "UserNeed",
    "VerificationReport",
    "Violation",
    "ConstraintVerifier",
    "RecommendationVerifier",
]
