"""Build recommendation bundles from verified candidates."""

from __future__ import annotations

from recharness.schema import (
    ConstraintCheck,
    RecommendationBundle,
    RecommendationCandidate,
    UserNeed,
    VerificationReport,
    Violation,
)


class BundleBuilder:
    """Separate eligible recommendations from rejected diagnostic candidates."""

    def build(
        self,
        need: UserNeed,
        ranked: list[RecommendationCandidate],
        top_k: int,
        trace_id: str,
    ) -> RecommendationBundle:
        recommended = [
            candidate
            for candidate in ranked
            if not _has_hard_violation(candidate)
        ][:top_k]
        recommended_ids = {candidate.product.product_id for candidate in recommended}
        rejected = [
            candidate
            for candidate in ranked
            if candidate.product.product_id not in recommended_ids
            and (_has_hard_violation(candidate) or (candidate.constraint_score or 0) < 1.0)
        ]

        constraint_report = _constraint_report(need, ranked)

        return RecommendationBundle(
            user_need=need,
            candidates=ranked,
            recommended=recommended,
            rejected=rejected,
            comparison_axes=_comparison_axes(need, ranked),
            constraint_report=constraint_report,
            clarification_questions=[],
            summary_for_agent=_summary_for_agent(recommended, rejected),
            trace_id=trace_id,
        )


def _has_hard_violation(candidate: RecommendationCandidate) -> bool:
    return any(violation.severity == "hard" for violation in candidate.violations)


def _constraint_report(
    need: UserNeed,
    candidates: list[RecommendationCandidate],
) -> VerificationReport:
    checks: list[ConstraintCheck] = []
    violations: list[Violation] = []
    for candidate in candidates:
        checks.extend(candidate.matched_constraints)
        violations.extend(candidate.violations)

    status = "pass"
    if any(violation.severity == "hard" for violation in violations):
        status = "fail"
    elif violations:
        status = "warning"

    return VerificationReport(
        status=status,
        user_need=need,
        checks=checks,
        violations=violations,
        product_grounded=bool(candidates),
        summary=(
            f"Verified {len(candidates)} retrieved candidates; "
            f"hard_violations={sum(1 for violation in violations if violation.severity == 'hard')}."
        ),
    )


def _comparison_axes(
    need: UserNeed,
    candidates: list[RecommendationCandidate],
) -> list[str]:
    axes: list[str] = []
    axes.extend(constraint.field for constraint in need.hard_constraints)
    axes.extend(preference.field for preference in need.soft_preferences)
    axes.extend(preference.field for preference in need.negative_preferences)

    common_attributes = [
        "attributes.capacity_liters",
        "attributes.laptop_size_inches",
        "attributes.weight_kg",
        "attributes.water_resistance",
        "availability",
        "price.amount",
    ]
    present_attributes = {
        f"attributes.{key}"
        for candidate in candidates
        for key in candidate.product.attributes
    }
    for axis in common_attributes:
        if axis in present_attributes or axis in {"availability", "price.amount"}:
            axes.append(axis)

    return _dedupe(axes)


def _summary_for_agent(
    recommended: list[RecommendationCandidate],
    rejected: list[RecommendationCandidate],
) -> str:
    if not recommended:
        return (
            "No retrieved products passed hard constraints. Do not recommend rejected products "
            "without explicitly qualifying their violations. Do not overstate waterproof, "
            "lightweight, availability, or laptop-fit claims."
        )

    names = ", ".join(candidate.product.title for candidate in recommended[:3])
    rejected_note = ""
    if rejected:
        rejected_note = f" Rejected {len(rejected)} candidate(s) with hard constraint issues."
    return (
        f"Recommend {recommended[0].product.title} as the safest choice. "
        f"Other viable options: {names}.{rejected_note} Do not overstate waterproof, "
        "lightweight, availability, or laptop-fit claims."
    )


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped
