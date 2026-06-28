"""Pattern-based product claim verification."""

from __future__ import annotations

import re
from typing import Any

from recharness.domains import get_domain_adapter
from recharness.schema import ClaimIssue, ProductItem


class ClaimVerifier:
    """Check high-signal recommendation claims against catalog attributes."""

    def verify_claims(
        self,
        product: ProductItem,
        agent_answer: str,
        local_text: str | None = None,
    ) -> list[ClaimIssue]:
        text = local_text if local_text is not None else agent_answer
        answer = text.lower()
        issues: list[ClaimIssue] = []

        issues.extend(_water_resistance_issues(product, answer))
        issues.extend(_price_issues(product, text))
        issues.extend(_laptop_fit_issues(product, answer))
        issues.extend(_weight_issues(product, answer))
        issues.extend(_availability_issues(product, answer))
        issues.extend(_noise_cancellation_issues(product, answer))
        issues.extend(_domain_claim_issues(product, text))

        return _dedupe_issues(issues)


def _water_resistance_issues(product: ProductItem, answer: str) -> list[ClaimIssue]:
    if not _claims_waterproof(answer):
        return []
    observed = str(product.attributes.get("water_resistance", "unknown"))
    if observed.lower() == "waterproof":
        return []
    return [
        _claim_issue(
            product,
            claim_type="water_resistance",
            issue_type="overstated",
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
                _claim_issue(
                    product,
                    claim_type="price",
                    issue_type="incorrect",
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
                _claim_issue(
                    product,
                    claim_type="laptop_fit",
                    issue_type="overstated",
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
    claimed = _claimed_weight(answer)
    if claimed is None:
        return []
    observed = product.attributes.get("weight_kg")
    if observed is None:
        return []
    threshold = 0.8 if claimed == "ultralight" else 1.0
    if float(observed) <= threshold:
        return []
    return [
        _claim_issue(
            product,
            claim_type="weight",
            issue_type="overstated",
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
    if not _claims_available(answer):
        return []
    if product.availability == "in_stock":
        return []
    return [
        _claim_issue(
            product,
            claim_type="availability",
            issue_type="incorrect",
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


def _noise_cancellation_issues(product: ProductItem, answer: str) -> list[ClaimIssue]:
    if not _claims_active_noise_cancellation(answer):
        return []
    observed = str(product.attributes.get("noise_cancellation", "unknown"))
    if observed.lower() == "anc":
        return []
    return [
        _claim_issue(
            product,
            claim_type="noise_cancellation",
            issue_type="overstated",
            severity="warning",
            field="attributes.noise_cancellation",
            claimed_value="anc",
            observed_value=observed,
            message=(
                f"{product.title}: active noise cancellation claim is overstated; "
                f"catalog noise_cancellation={observed}"
            ),
        )
    ]


def _claims_waterproof(answer: str) -> bool:
    return (
        "waterproof" in answer
        or "完全防水" in answer
        or "必须防水" in answer
        or "防水" in answer
    )


def _claimed_weight(answer: str) -> str | None:
    if "ultralight" in answer or "超轻" in answer:
        return "ultralight"
    if (
        "lightweight" in answer
        or "轻量" in answer
        or "轻便" in answer
        or "不重" in answer
    ):
        return "lightweight"
    return None


def _claims_available(answer: str) -> bool:
    return (
        "in stock" in answer
        or "available" in answer
        or "有货" in answer
        or "现货" in answer
        or "可购买" in answer
        or "库存充足" in answer
    )


def _claims_active_noise_cancellation(answer: str) -> bool:
    return (
        "active noise cancellation" in answer
        or "active noise cancelling" in answer
        or " anc" in f" {answer}"
        or "有降噪" in answer
        or "主动降噪" in answer
    )


def _domain_claim_issues(product: ProductItem, text: str) -> list[ClaimIssue]:
    adapter = get_domain_adapter(product.category)
    if adapter is None:
        return []
    try:
        return adapter.verify_claims(product, text)
    except Exception as exc:
        return [
            _claim_issue(
                product,
                claim_type="domain_adapter",
                issue_type="unsupported",
                severity="warning",
                field="category",
                claimed_value=product.category,
                observed_value=product.category,
                message=f"{product.title}: domain adapter claim check failed: {exc}",
            )
        ]


def _dedupe_issues(issues: list[ClaimIssue]) -> list[ClaimIssue]:
    deduped: list[ClaimIssue] = []
    seen: set[tuple[Any, ...]] = set()
    for issue in issues:
        key = (
            issue.product_id,
            issue.claim_type,
            issue.issue_type,
            issue.field,
            str(issue.claimed_value),
            str(issue.observed_value),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped


def _claim_issue(product: ProductItem, **kwargs: Any) -> ClaimIssue:
    return ClaimIssue(
        product_id=product.product_id,
        product_title=product.title,
        **kwargs,
    )


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
