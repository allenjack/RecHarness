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
            constraint_score = 1.0 if report.status == "pass" else 0.0
            preference_score = _negative_preference_score(scored.product.attributes, need)
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
