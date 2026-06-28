"""Transparent deterministic candidate ranking."""

from __future__ import annotations

from typing import Any

from recharness.retrieval import ScoredProduct
from recharness.schema import RecommendationCandidate, UserNeed
from recharness.verification import ConstraintVerifier


class SimpleRanker:
    """Rank candidates with transparent constraint, preference, and retrieval scores."""

    def __init__(self, verifier: ConstraintVerifier | None = None) -> None:
        self.verifier = verifier or ConstraintVerifier()

    def rank(
        self,
        need: UserNeed,
        candidates: list[ScoredProduct],
        top_k: int = 5,
    ) -> list[RecommendationCandidate]:
        ranked: list[RecommendationCandidate] = []

        for scored in candidates:
            report = self.verifier.verify_product(scored.product, need.hard_constraints)
            constraint_score = _constraint_score(report.checks)
            preference_score = _preference_score(scored.product.attributes, need)
            final_score = round(
                0.5 * constraint_score
                + 0.3 * scored.score
                + 0.2 * preference_score,
                6,
            )

            ranked.append(
                RecommendationCandidate(
                    product=scored.product,
                    retrieval_score=scored.score,
                    preference_score=preference_score,
                    constraint_score=constraint_score,
                    final_score=final_score,
                    matched_constraints=report.checks,
                    violations=report.violations,
                    evidence=scored.product.evidence,
                )
            )

        return sorted(
            ranked,
            key=lambda candidate: (
                -(candidate.final_score or 0),
                candidate.product.product_id,
            ),
        )[:top_k]


def _constraint_score(checks) -> float:
    if not checks:
        return 1.0
    satisfied = sum(1 for check in checks if check.satisfied)
    return round(satisfied / len(checks), 6)


def _preference_score(attributes: dict[str, Any], need: UserNeed) -> float:
    positive_score = _positive_preference_score(attributes, need)
    negative_score = _negative_preference_score(attributes, need)
    if not need.soft_preferences:
        return negative_score
    return round(0.7 * positive_score + 0.3 * negative_score, 6)


def _positive_preference_score(attributes: dict[str, Any], need: UserNeed) -> float:
    if not need.soft_preferences:
        return 1.0
    scores: list[float] = []
    for preference in need.soft_preferences:
        observed = _resolve_attribute_path(attributes, preference.field)
        scores.append(_positive_match_score(observed, preference.field, preference.value))
    return round(sum(scores) / len(scores), 6)


def _positive_match_score(observed: Any, field: str, expected: Any) -> float:
    if field == "attributes.weight_kg":
        return _weight_match_score(observed, str(expected))
    if field == "attributes.latency_ms":
        return _latency_match_score(observed, str(expected))
    if field == "attributes.battery_life_hours":
        return _battery_match_score(observed, str(expected))
    if observed is None:
        return 0.5
    return 1.0 if _contains(observed, expected) else 0.0


def _weight_match_score(observed: Any, expected: str) -> float:
    if observed is None:
        return 0.5
    try:
        weight = float(observed)
    except (TypeError, ValueError):
        return 0.5
    if expected == "ultralight":
        if weight <= 0.8:
            return 1.0
        if weight <= 1.0:
            return 0.5
        return 0.0
    if expected == "lightweight":
        if weight <= 1.0:
            return 1.0
        if weight <= 1.2:
            return 0.5
        return 0.0
    return 0.0


def _latency_match_score(observed: Any, expected: str) -> float:
    if observed is None:
        return 0.5
    try:
        latency = float(observed)
    except (TypeError, ValueError):
        return 0.5
    if expected == "low_latency":
        if latency <= 50:
            return 1.0
        if latency <= 80:
            return 0.5
        return 0.0
    return 0.0


def _battery_match_score(observed: Any, expected: str) -> float:
    if observed is None:
        return 0.5
    try:
        hours = float(observed)
    except (TypeError, ValueError):
        return 0.5
    if expected == "long_battery":
        if hours >= 30:
            return 1.0
        if hours >= 20:
            return 0.5
        return 0.0
    return 0.0


def _negative_preference_score(attributes: dict[str, Any], need: UserNeed) -> float:
    score = 1.0
    for preference in need.negative_preferences:
        observed = _resolve_attribute_path(attributes, preference.field)
        if _contains(observed, preference.value):
            score -= preference.weight
    return max(0.0, round(score, 6))


def _resolve_attribute_path(attributes: dict[str, Any], field: str) -> Any:
    if field.startswith("attributes."):
        field = field.removeprefix("attributes.")
    value: Any = attributes
    for part in field.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def _contains(observed: Any, expected: Any) -> bool:
    if observed is None:
        return False
    if isinstance(observed, str):
        return str(expected).lower() in observed.lower()
    if isinstance(observed, (list, tuple, set)):
        expected_text = str(expected).lower()
        return any(str(item).lower() == expected_text for item in observed)
    return observed == expected
