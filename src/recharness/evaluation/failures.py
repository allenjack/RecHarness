"""Failure taxonomy helpers for evaluation records."""

from __future__ import annotations

from recharness.schema import RecommendationBundle, VerificationReport


def failure_labels_from_report(report: VerificationReport) -> list[str]:
    labels: list[str] = []
    if not report.product_grounded:
        labels.append("no_grounded_product")
    if report.unresolved_mentions:
        labels.append("product_hallucination")
    if any(violation.severity == "hard" for violation in report.violations):
        labels.append("hard_constraint_violation")
    if report.unsupported_claims:
        labels.append("unsupported_claim")
    if report.overstated_claims:
        labels.append("overstated_claim")
    if report.incorrect_claims:
        labels.append("incorrect_claim")
    return _dedupe(labels)


def failure_labels_from_bundle(bundle: RecommendationBundle) -> list[str]:
    labels: list[str] = []
    if not bundle.recommended and bundle.user_need.missing_slots:
        labels.append("premature_recommendation")
    if any(
        any(violation.severity == "hard" for violation in candidate.violations)
        for candidate in bundle.recommended
    ):
        labels.append("hard_constraint_violation")
    if bundle.constraint_report.violations:
        labels.append("candidate_pool_contains_violations")
    if bundle.rejected:
        labels.append("rejected_candidate_present")
    return _dedupe(labels)


def _dedupe(labels: list[str]) -> list[str]:
    deduped: list[str] = []
    for label in labels:
        if label not in deduped:
            deduped.append(label)
    return deduped
