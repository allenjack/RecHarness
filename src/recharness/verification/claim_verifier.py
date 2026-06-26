"""Pattern-based product claim verification."""

from __future__ import annotations

import re
from typing import Any

from recharness.schema import ClaimIssue, ProductItem


class ClaimVerifier:
    """Check high-signal recommendation claims against catalog attributes."""

    def verify_claims(self, product: ProductItem, agent_answer: str) -> list[ClaimIssue]:
        answer = agent_answer.lower()
        issues: list[ClaimIssue] = []

        issues.extend(_water_resistance_issues(product, answer))
        issues.extend(_price_issues(product, agent_answer))
        issues.extend(_laptop_fit_issues(product, answer))
        issues.extend(_weight_issues(product, answer))
        issues.extend(_availability_issues(product, answer))

        return issues


def _water_resistance_issues(product: ProductItem, answer: str) -> list[ClaimIssue]:
    if "waterproof" not in answer:
        return []
    observed = str(product.attributes.get("water_resistance", "unknown"))
    if observed.lower() == "waterproof":
        return []
    return [
        ClaimIssue(
            claim_type="water_resistance",
            severity="warning",
            field="attributes.water_resistance",
            claimed_value="waterproof",
            observed_value=observed,
            message=(
                f"{product.title}: waterproof claim is unsupported; "
                f"catalog water_resistance={observed}"
            ),
        )
    ]


def _price_issues(product: ProductItem, agent_answer: str) -> list[ClaimIssue]:
    if product.price is None:
        return []
    issues: list[ClaimIssue] = []
    for claimed in _money_amounts(agent_answer):
        observed = product.price.amount
        if abs(float(claimed) - float(observed)) > 0.01:
            issues.append(
                ClaimIssue(
                    claim_type="price",
                    severity="hard",
                    field="price.amount",
                    claimed_value=claimed,
                    observed_value=_clean_number(observed),
                    message=(
                        f"{product.title}: price claim {claimed} does not match "
                        f"catalog price {observed:g} {product.price.currency}"
                    ),
                )
            )
    return issues


def _laptop_fit_issues(product: ProductItem, answer: str) -> list[ClaimIssue]:
    observed = product.attributes.get("laptop_size_inches")
    if observed is None:
        return []
    issues: list[ClaimIssue] = []
    for claimed in _laptop_inches(answer):
        if float(claimed) > float(observed):
            issues.append(
                ClaimIssue(
                    claim_type="laptop_fit",
                    severity="hard",
                    field="attributes.laptop_size_inches",
                    claimed_value=claimed,
                    observed_value=_clean_number(observed),
                    message=(
                        f"{product.title}: laptop fit claim {claimed}-inch exceeds "
                        f"catalog laptop fit {observed}-inch"
                    ),
                )
            )
    return issues


def _weight_issues(product: ProductItem, answer: str) -> list[ClaimIssue]:
    if "lightweight" not in answer and "ultralight" not in answer:
        return []
    observed = product.attributes.get("weight_kg")
    if observed is None:
        return []
    threshold = 1.0 if "lightweight" in answer else 0.8
    claimed = "lightweight" if "lightweight" in answer else "ultralight"
    if float(observed) <= threshold:
        return []
    return [
        ClaimIssue(
            claim_type="weight",
            severity="warning",
            field="attributes.weight_kg",
            claimed_value=claimed,
            observed_value=_clean_number(observed),
            message=(
                f"{product.title}: {claimed} claim is overstated; "
                f"catalog weight is {observed}kg"
            ),
        )
    ]


def _availability_issues(product: ProductItem, answer: str) -> list[ClaimIssue]:
    if "in stock" not in answer and "available" not in answer:
        return []
    if product.availability == "in_stock":
        return []
    return [
        ClaimIssue(
            claim_type="availability",
            severity="hard",
            field="availability",
            claimed_value="in_stock",
            observed_value=product.availability,
            message=(
                f"{product.title}: availability claim is unsupported; "
                f"catalog availability={product.availability}"
            ),
        )
    ]


def _money_amounts(text: str) -> list[int | float]:
    amounts: list[int | float] = []
    patterns = [
        r"(?:rmb|cny|¥|\$)\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:rmb|cny|元|块)",
    ]
    for pattern in patterns:
        amounts.extend(_clean_number(match) for match in re.findall(pattern, text, flags=re.I))
    return _dedupe(amounts)


def _laptop_inches(text: str) -> list[int | float]:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:-| )?\s*inch(?:es)?\s*laptop",
        r"(\d+(?:\.\d+)?)\s*(?:寸|英寸)\s*(?:电脑|笔记本)?",
    ]
    values: list[int | float] = []
    for pattern in patterns:
        values.extend(_clean_number(match) for match in re.findall(pattern, text, flags=re.I))
    return _dedupe(values)


def _clean_number(value: Any) -> int | float:
    parsed = float(value)
    if parsed.is_integer():
        return int(parsed)
    return parsed


def _dedupe(values: list[int | float]) -> list[int | float]:
    deduped: list[int | float] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped
