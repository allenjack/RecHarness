"""Agent recommendation verification against a local catalog."""

from __future__ import annotations

from collections.abc import Sequence

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
        products = resolve_mentioned_products(agent_answer, catalog)
        checks = []
        violations = []
        claim_issues: list[ClaimIssue] = []
        unsupported_claims: list[str] = []
        repair_suggestions: list[str] = []

        if not products:
            return VerificationReport(
                status="fail",
                summary="No catalog products were resolved from the agent answer.",
                repair_suggestions=["Mention a product title that exists in the catalog."],
            )

        for product in products:
            report = self.constraint_verifier.verify_product(product, need.hard_constraints)
            checks.extend(report.checks)
            violations.extend(report.violations)
            product_claim_issues = self.claim_verifier.verify_claims(product, agent_answer)
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
            checks=checks,
            violations=violations,
            claim_issues=claim_issues,
            unsupported_claims=unsupported_claims,
            repair_suggestions=repair_suggestions,
            summary=_summary(status, products, violations, claim_issues),
        )


def resolve_mentioned_products(
    agent_answer: str,
    catalog: Sequence[ProductItem],
) -> list[ProductItem]:
    answer = agent_answer.lower()
    return [
        product
        for product in catalog
        if product.title.lower() in answer or product.product_id.lower() in answer
    ]


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
