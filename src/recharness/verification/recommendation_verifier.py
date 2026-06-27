"""Agent recommendation verification against a local catalog."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from recharness.schema import ClaimIssue, ProductItem, UserNeed, VerificationReport
from recharness.verification.claim_verifier import ClaimVerifier
from recharness.verification.constraint_verifier import ConstraintVerifier


class RecommendationVerifier:
    """Resolve mentioned products and verify constraints and claims."""

    def __init__(
        self,
        constraint_verifier: ConstraintVerifier | None = None,
        claim_verifier: ClaimVerifier | None = None,
    ) -> None:
        self.constraint_verifier = constraint_verifier or ConstraintVerifier()
        self.claim_verifier = claim_verifier or ClaimVerifier()

    def verify(
        self,
        need: UserNeed,
        agent_answer: str,
        catalog: Sequence[ProductItem],
    ) -> VerificationReport:
        mentions = resolve_product_mentions(agent_answer, catalog)
        products = [mention.product for mention in mentions]
        mentioned_products = _mentioned_product_strings(agent_answer, mentions)
        unresolved_mentions = _unresolved_mentions(agent_answer, mentions)
        checks = []
        violations = []
        claim_issues: list[ClaimIssue] = []
        unsupported_claims: list[str] = []
        repair_suggestions: list[str] = []

        if not products:
            return VerificationReport(
                status="fail",
                user_need=need,
                mentioned_products=mentioned_products,
                unresolved_mentions=unresolved_mentions,
                product_grounded=False,
                summary="No catalog products were resolved from the agent answer.",
                repair_suggestions=["Mention a product title that exists in the catalog."],
            )

        for mention in mentions:
            product = mention.product
            report = self.constraint_verifier.verify_product(product, need.hard_constraints)
            checks.extend(report.checks)
            violations.extend(report.violations)
            local_text = _local_text(agent_answer, mention, mentions)
            product_claim_issues = self.claim_verifier.verify_claims(
                product,
                agent_answer,
                local_text=local_text,
            )
            claim_issues.extend(product_claim_issues)
            unsupported_claims.extend(issue.message for issue in product_claim_issues)
            if report.violations:
                repair_suggestions.append(
                    f"Replace or qualify {product.title}; it violates parsed hard constraints."
                )
            if any(issue.severity == "hard" for issue in product_claim_issues):
                repair_suggestions.append(
                    f"Correct or remove hard factual claims about {product.title}."
                )

        status = "pass"
        if any(violation.severity == "hard" for violation in violations) or any(
            issue.severity == "hard" for issue in claim_issues
        ):
            status = "fail"
        elif claim_issues or violations:
            status = "warning"

        return VerificationReport(
            status=status,
            user_need=need,
            mentioned_products=mentioned_products,
            resolved_products=products,
            unresolved_mentions=unresolved_mentions,
            product_grounded=bool(products),
            checks=checks,
            violations=violations,
            claim_issues=claim_issues,
            unsupported_claims=unsupported_claims,
            repair_suggestions=repair_suggestions,
            summary=_summary(status, products, violations, claim_issues),
        )


@dataclass(frozen=True)
class ProductMention:
    product: ProductItem
    text: str
    start: int
    end: int


def resolve_product_mentions(
    agent_answer: str,
    catalog: Sequence[ProductItem],
) -> list[ProductMention]:
    answer = agent_answer.lower()
    mentions: list[ProductMention] = []

    for product in catalog:
        match = _best_product_match(product, agent_answer, answer)
        if match is not None:
            start, end = match
            mentions.append(
                ProductMention(
                    product=product,
                    text=agent_answer[start:end],
                    start=start,
                    end=end,
                )
            )

    return sorted(
        _dedupe_mentions(mentions),
        key=lambda mention: (mention.start, mention.product.product_id),
    )


def resolve_mentioned_products(
    agent_answer: str,
    catalog: Sequence[ProductItem],
) -> list[ProductItem]:
    return [mention.product for mention in resolve_product_mentions(agent_answer, catalog)]


def _best_product_match(
    product: ProductItem,
    original_answer: str,
    normalized_answer: str,
) -> tuple[int, int] | None:
    product_id_match = _literal_match(normalized_answer, product.product_id.lower())
    title_match = _literal_match(normalized_answer, product.title.lower())
    if product_id_match is not None and title_match is not None:
        return min(product_id_match, title_match, key=lambda item: item[0])
    if product_id_match is not None:
        return product_id_match
    if title_match is not None:
        return title_match

    brand_partial = _brand_partial_match(product, original_answer, normalized_answer)
    if brand_partial is not None:
        return brand_partial

    return _token_overlap_match(product, original_answer, normalized_answer)


def _literal_match(answer: str, needle: str) -> tuple[int, int] | None:
    if not needle:
        return None
    start = answer.find(needle)
    if start < 0:
        return None
    return start, start + len(needle)


def _brand_partial_match(
    product: ProductItem,
    original_answer: str,
    normalized_answer: str,
) -> tuple[int, int] | None:
    if not product.brand or product.brand.lower() not in normalized_answer:
        return None
    title_tokens = _distinctive_tokens(product.title)
    answer_tokens = _answer_token_spans(original_answer)
    matched = [
        span
        for token, span in answer_tokens
        if token == product.brand.lower() or token in title_tokens
    ]
    matched_tokens = {original_answer[start:end].lower() for start, end in matched}
    if product.brand.lower() in matched_tokens and len(matched) >= 2:
        return min(start for start, _ in matched), max(end for _, end in matched)
    return None


def _token_overlap_match(
    product: ProductItem,
    original_answer: str,
    normalized_answer: str,
) -> tuple[int, int] | None:
    title_tokens = _distinctive_tokens(product.title)
    if len(title_tokens) < 2:
        return None
    answer_tokens = _answer_token_spans(original_answer)
    matched = [(start, end) for token, (start, end) in answer_tokens if token in title_tokens]
    if len(matched) >= min(3, len(title_tokens)):
        return min(start for start, _ in matched), max(end for _, end in matched)
    return None


def _distinctive_tokens(text: str) -> set[str]:
    generic = {
        "a",
        "an",
        "and",
        "benchmark",
        "backpack",
        "bag",
        "pack",
        "the",
        "with",
    }
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) >= 3
        and token not in generic
        and not any(character.isdigit() for character in token)
    }


def _answer_token_spans(text: str) -> list[tuple[str, tuple[int, int]]]:
    return [
        (match.group(0).lower(), (match.start(), match.end()))
        for match in re.finditer(r"[a-zA-Z0-9]+", text)
    ]


def _dedupe_mentions(mentions: list[ProductMention]) -> list[ProductMention]:
    deduped: dict[str, ProductMention] = {}
    for mention in mentions:
        current = deduped.get(mention.product.product_id)
        if current is None or (mention.end - mention.start) > (current.end - current.start):
            deduped[mention.product.product_id] = mention
    return list(deduped.values())


def _local_text(
    agent_answer: str,
    mention: ProductMention,
    mentions: list[ProductMention],
) -> str:
    later_starts = [
        other.start
        for other in mentions
        if other.product.product_id != mention.product.product_id and other.start > mention.start
    ]
    end = min(later_starts) if later_starts else len(agent_answer)
    return agent_answer[mention.start:end]


def _mentioned_product_strings(
    agent_answer: str,
    mentions: list[ProductMention],
) -> list[str]:
    values = [mention.text.strip() for mention in mentions]
    values.extend(_unresolved_mentions(agent_answer, mentions))
    return _dedupe_strings(values)


def _unresolved_mentions(
    agent_answer: str,
    mentions: list[ProductMention],
) -> list[str]:
    candidates = _recommendation_phrases(agent_answer)
    resolved_spans = [(mention.start, mention.end) for mention in mentions]
    unresolved: list[str] = []
    for text, start, end in candidates:
        if any(_overlaps((start, end), span) for span in resolved_spans):
            continue
        unresolved.append(text)
    return _dedupe_strings(unresolved)


def _recommendation_phrases(agent_answer: str) -> list[tuple[str, int, int]]:
    phrases: list[tuple[str, int, int]] = []
    pattern = re.compile(
        r"(?:recommend|推荐)\s+(?:the\s+)?([A-Z][A-Za-z0-9]*(?:[ -][A-Za-z0-9]+){0,5})"
    )
    for match in pattern.finditer(agent_answer):
        text = re.split(
            r"\s+(?:costs?|is|fits?|and)\b|[。.!?]",
            match.group(1),
            maxsplit=1,
        )[0].strip()
        if text:
            start = match.start(1)
            end = start + len(text)
            phrases.append((text, start, end))
    return phrases


def _overlaps(first: tuple[int, int], second: tuple[int, int]) -> bool:
    return first[0] < second[1] and second[0] < first[1]


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return deduped


def _summary(
    status: str,
    products: Sequence[ProductItem],
    violations,
    claim_issues: list[ClaimIssue],
) -> str:
    titles = ", ".join(product.title for product in products)
    if status == "pass":
        return f"Resolved catalog recommendation passes verification: {titles}."
    return (
        f"Resolved catalog recommendation needs review: {titles}. "
        f"violations={len(violations)}, claim_issues={len(claim_issues)}"
    )
