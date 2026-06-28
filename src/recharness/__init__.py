"""Public API for the RecHarness foundation package."""

from recharness.bundle import BundleBuilder
from recharness.catalog import (
    CatalogConfig,
    CatalogConfigError,
    CatalogIssue,
    CatalogLoadError,
    CatalogStats,
    CatalogValidationReport,
    JsonlCatalog,
    MultiCatalogConfig,
    load_multi_catalog_config,
)
from recharness.core import AgentHarnessRouter, HarnessVariant, RecHarness
from recharness.evaluation import (
    AgentOutput,
    EvalMission,
    EvalRecord,
    EvalResult,
    EvalRunner,
    failure_labels_from_bundle,
    failure_labels_from_report,
)
from recharness.preference import RuleBasedPreferenceParser
from recharness.ranking import SimpleRanker
from recharness.retrieval import (
    AttributeFilterRetriever,
    HybridRetriever,
    KeywordRetriever,
    ScoredProduct,
)
from recharness.schema import (
    ClaimIssue,
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
from recharness.schema.tools import (
    AssistRequest,
    AssistResponse,
    ParseRequest,
    ParseResponse,
    VerifyRequest,
    VerifyResponse,
)
from recharness.tracing import JsonlTraceLogger
from recharness.verification import ClaimVerifier, ConstraintVerifier, RecommendationVerifier

__all__ = [
    "CatalogIssue",
    "CatalogConfig",
    "CatalogConfigError",
    "CatalogLoadError",
    "CatalogStats",
    "CatalogValidationReport",
    "MultiCatalogConfig",
    "load_multi_catalog_config",
    "AgentHarnessRouter",
    "AssistRequest",
    "AssistResponse",
    "ClaimVerifier",
    "ClaimIssue",
    "AgentOutput",
    "Constraint",
    "ConstraintCheck",
    "AttributeFilterRetriever",
    "BundleBuilder",
    "Evidence",
    "EvalMission",
    "EvalRecord",
    "EvalResult",
    "EvalRunner",
    "HarnessVariant",
    "failure_labels_from_bundle",
    "failure_labels_from_report",
    "HybridRetriever",
    "JsonlCatalog",
    "JsonlTraceLogger",
    "KeywordRetriever",
    "Money",
    "ParseRequest",
    "ParseResponse",
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
    "VerifyRequest",
    "VerifyResponse",
    "Violation",
    "ConstraintVerifier",
    "RecommendationVerifier",
]
