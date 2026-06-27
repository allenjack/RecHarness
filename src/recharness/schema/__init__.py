"""Core Pydantic schemas for RecHarness."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecHarnessModel(BaseModel):
    """Base model with strict field names and assignment validation."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Money(RecHarnessModel):
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class Evidence(RecHarnessModel):
    field: str
    value: Any
    source_type: str
    source: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class Constraint(RecHarnessModel):
    field: str
    operator: Literal[
        "=",
        "!=",
        "<",
        "<=",
        ">",
        ">=",
        "contains",
        "not_contains",
        "exists",
    ]
    value: Any = None
    unit: str | None = None
    severity: Literal["hard", "soft"] = "hard"
    source: Literal["user", "profile", "system", "inferred"] = "user"


class Preference(RecHarnessModel):
    field: str
    value: Any
    weight: float = Field(default=1.0, ge=0, le=1)
    polarity: Literal["positive", "negative"] = "positive"
    source: Literal["user", "profile", "system", "inferred"] = "user"


class ProductItem(RecHarnessModel):
    product_id: str
    title: str
    category: str
    brand: str | None = None
    price: Money | None = None
    availability: Literal["in_stock", "out_of_stock", "unknown"] = "unknown"
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    review_summary: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    source: str | None = None


class UserNeed(RecHarnessModel):
    raw_query: str
    category: str | None = None
    scenario: list[str] = Field(default_factory=list)
    hard_constraints: list[Constraint] = Field(default_factory=list)
    soft_preferences: list[Preference] = Field(default_factory=list)
    negative_preferences: list[Preference] = Field(default_factory=list)
    missing_slots: list[str] = Field(default_factory=list)
    urgency: Literal["low", "normal", "high"] = "normal"


class ConstraintCheck(RecHarnessModel):
    constraint: Constraint
    observed_value: Any = None
    satisfied: bool
    message: str | None = None


class Violation(RecHarnessModel):
    constraint: Constraint
    observed_value: Any = None
    severity: Literal["hard", "soft"] = "hard"
    message: str


class ClaimIssue(RecHarnessModel):
    product_id: str | None = None
    product_title: str | None = None
    claim_type: str
    issue_type: Literal["unsupported", "overstated", "incorrect"] | None = None
    severity: Literal["warning", "hard"] = "warning"
    field: str
    claimed_value: Any
    observed_value: Any = None
    message: str


class VerificationReport(RecHarnessModel):
    status: Literal["pass", "fail", "warning"] = "pass"
    user_need: UserNeed | None = None
    mentioned_products: list[str] = Field(default_factory=list)
    resolved_products: list[ProductItem] = Field(default_factory=list)
    unresolved_mentions: list[str] = Field(default_factory=list)
    product_grounded: bool = False
    checks: list[ConstraintCheck] = Field(default_factory=list)
    violations: list[Violation] = Field(default_factory=list)
    claim_issues: list[ClaimIssue] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    repair_suggestions: list[str] = Field(default_factory=list)
    summary: str | None = None


class RecommendationCandidate(RecHarnessModel):
    product: ProductItem
    retrieval_score: float | None = Field(default=None, ge=0, le=1)
    preference_score: float | None = Field(default=None, ge=0, le=1)
    constraint_score: float | None = Field(default=None, ge=0, le=1)
    final_score: float | None = Field(default=None, ge=0, le=1)
    matched_constraints: list[ConstraintCheck] = Field(default_factory=list)
    violations: list[Violation] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class RecommendationBundle(RecHarnessModel):
    user_need: UserNeed
    candidates: list[RecommendationCandidate]
    recommended: list[RecommendationCandidate]
    rejected: list[RecommendationCandidate] = Field(default_factory=list)
    comparison_axes: list[str] = Field(default_factory=list)
    constraint_report: VerificationReport
    clarification_questions: list[dict[str, Any]] = Field(default_factory=list)
    summary_for_agent: str
    trace_id: str


class TraceEvent(RecHarnessModel):
    trace_id: str
    step: int = Field(ge=0)
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
