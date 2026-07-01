"""Deterministic answer repair utilities."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import Field

from recharness.schema import (
    ProductItem,
    RecHarnessModel,
    RecommendationBundle,
    VerificationReport,
)
from recharness.schema.tools import AssistResponse, VerifyResponse


class RepairResult(RecHarnessModel):
    status: Literal["unchanged", "repaired", "qualified", "failed"]
    repaired_answer: str
    changes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def repair_answer_from_verification(
    answer: str,
    verify_response: VerifyResponse | VerificationReport | dict[str, Any],
    assist_response: AssistResponse | RecommendationBundle | dict[str, Any] | None = None,
) -> RepairResult:
    """Repair or qualify an answer using only structured RecHarness evidence."""

    report = _report_from_verify_response(verify_response)
    errors = _errors_from_verify_response(verify_response)
    if report is None:
        return RepairResult(
            status="failed",
            repaired_answer=answer,
            warnings=errors or ["No verification report was available for repair."],
        )

    if _report_status(report) == "pass":
        return RepairResult(status="unchanged", repaired_answer=answer)

    hard_problem = _has_hard_violation(report) or _has_hard_claim_issue(report)
    safe_product = _safe_recommended_product(assist_response)
    if hard_problem and safe_product is not None:
        return RepairResult(
            status="repaired",
            repaired_answer=_replacement_answer(safe_product, answer),
            changes=[
                "Replaced a hard constraint or hard claim failure with a safe assist candidate."
            ],
        )

    repaired = answer
    changes: list[str] = []
    warnings: list[str] = []

    for issue in _claim_issues(report):
        repaired, issue_changes = _repair_claim_issue(repaired, issue)
        changes.extend(issue_changes)
        if not issue_changes:
            warnings.append(_issue_warning(issue))

    if changes:
        return RepairResult(
            status="repaired",
            repaired_answer=_append_repair_note(repaired, answer),
            changes=changes,
            warnings=warnings,
        )

    warnings.extend(_repair_suggestions(report))
    warnings.extend(_unresolved_warning(report))
    if not warnings:
        warnings.append("Verification did not pass, but no deterministic repair was available.")
    return RepairResult(
        status="qualified",
        repaired_answer=_qualified_answer(answer),
        warnings=warnings,
    )


def repair_or_qualify_answer(
    answer: str,
    verify_response: VerifyResponse | VerificationReport | dict[str, Any],
    assist_response: AssistResponse | RecommendationBundle | dict[str, Any] | None = None,
) -> str:
    """Return only the answer text for examples and agent-loop integrations."""

    return repair_answer_from_verification(
        answer,
        verify_response,
        assist_response=assist_response,
    ).repaired_answer


def _report_from_verify_response(
    verify_response: VerifyResponse | VerificationReport | dict[str, Any],
) -> VerificationReport | dict[str, Any] | None:
    if isinstance(verify_response, VerificationReport):
        return verify_response
    if isinstance(verify_response, VerifyResponse):
        return verify_response.report
    if isinstance(verify_response, dict):
        report = verify_response.get("report")
        return report if isinstance(report, dict) else None
    return None


def _errors_from_verify_response(
    verify_response: VerifyResponse | VerificationReport | dict[str, Any],
) -> list[str]:
    if isinstance(verify_response, VerifyResponse):
        return list(verify_response.errors)
    if isinstance(verify_response, dict):
        return [str(error) for error in verify_response.get("errors", [])]
    return []


def _report_status(report: VerificationReport | dict[str, Any]) -> str:
    if isinstance(report, VerificationReport):
        return report.status
    return str(report.get("status", "fail"))


def _has_hard_violation(report: VerificationReport | dict[str, Any]) -> bool:
    return any(_field(violation, "severity") == "hard" for violation in _violations(report))


def _has_hard_claim_issue(report: VerificationReport | dict[str, Any]) -> bool:
    return any(_field(issue, "severity") == "hard" for issue in _claim_issues(report))


def _claim_issues(report: VerificationReport | dict[str, Any]) -> list[Any]:
    if isinstance(report, VerificationReport):
        return list(report.claim_issues)
    return list(report.get("claim_issues", []))


def _violations(report: VerificationReport | dict[str, Any]) -> list[Any]:
    if isinstance(report, VerificationReport):
        return list(report.violations)
    return list(report.get("violations", []))


def _repair_suggestions(report: VerificationReport | dict[str, Any]) -> list[str]:
    if isinstance(report, VerificationReport):
        return list(report.repair_suggestions)
    return [str(suggestion) for suggestion in report.get("repair_suggestions", [])]


def _unresolved_warning(report: VerificationReport | dict[str, Any]) -> list[str]:
    if isinstance(report, VerificationReport):
        mentions = report.unresolved_mentions
    else:
        mentions = report.get("unresolved_mentions", [])
    if not mentions:
        return []
    return [f"Unresolved catalog mention(s): {', '.join(str(item) for item in mentions)}"]


def _safe_recommended_product(
    assist_response: AssistResponse | RecommendationBundle | dict[str, Any] | None,
) -> ProductItem | dict[str, Any] | None:
    if assist_response is None:
        return None
    if isinstance(assist_response, AssistResponse):
        bundle = assist_response.bundle
    elif isinstance(assist_response, RecommendationBundle):
        bundle = assist_response
    else:
        bundle = assist_response.get("bundle")
    if bundle is None:
        return None
    recommended = (
        bundle.recommended
        if not isinstance(bundle, dict)
        else bundle.get("recommended", [])
    )
    for candidate in recommended:
        violations = (
            candidate.violations
            if not isinstance(candidate, dict)
            else candidate.get("violations", [])
        )
        if any(_field(violation, "severity") == "hard" for violation in violations):
            continue
        product = candidate.product if not isinstance(candidate, dict) else candidate.get("product")
        if product is not None:
            return product
    return None


def _repair_claim_issue(answer: str, issue: Any) -> tuple[str, list[str]]:
    claim_type = str(_field(issue, "claim_type") or "")
    observed = _field(issue, "observed_value")
    claimed = _field(issue, "claimed_value")
    updated = answer
    changes: list[str] = []

    if claim_type == "noise_cancellation":
        updated = _repair_noise_cancellation(updated, observed)
    elif claim_type == "battery_life":
        updated = _replace_numeric_claim(updated, claimed, observed, "续航", "小时", "h")
    elif claim_type == "price":
        updated = _replace_numeric_claim(updated, claimed, observed, "售价", "元", "RMB")
    elif claim_type == "weight":
        updated = _replace_numeric_claim(updated, claimed, observed, "重量", "kg", "kg")
    elif claim_type == "laptop_fit":
        updated = _replace_numeric_claim(updated, claimed, observed, "", "寸", "inch")
    elif claim_type == "availability" and observed is not None:
        updated = _append_fact_note(updated, f"local catalog availability is {observed}")

    if updated != answer:
        changes.append(f"Corrected {claim_type} using catalog value {observed!r}.")
    return updated, changes


def _repair_noise_cancellation(answer: str, observed: Any) -> str:
    observed_text = str(observed).lower()
    if observed_text in {"none", "false", "no", ""}:
        updated = answer.replace("，有主动降噪", "")
        updated = updated.replace(", with active noise cancellation", "")
        updated = updated.replace("with active noise cancellation", "without catalog-listed ANC")
        updated = updated.replace("主动降噪", "本地目录未标注主动降噪")
        return updated
    return _append_fact_note(answer, f"local catalog noise_cancellation is {observed}")


def _replace_numeric_claim(
    answer: str,
    claimed: Any,
    observed: Any,
    chinese_prefix: str,
    chinese_suffix: str,
    english_suffix: str,
) -> str:
    if claimed is None or observed is None:
        return answer
    claimed_text = _number_text(claimed)
    observed_text = _number_text(observed)
    replacements = [
        (
            f"{chinese_prefix}{claimed_text}{chinese_suffix}",
            f"{chinese_prefix}{observed_text}{chinese_suffix}",
        ),
        (f"{claimed_text}{english_suffix}", f"{observed_text}{english_suffix}"),
        (f"{claimed_text} {english_suffix}", f"{observed_text} {english_suffix}"),
    ]
    updated = answer
    for old, new in replacements:
        if old and old in updated:
            updated = updated.replace(old, new)
    if updated != answer:
        return updated
    return re.sub(
        rf"(?<!\d){re.escape(claimed_text)}(?!\d)",
        observed_text,
        answer,
        count=1,
    )


def _replacement_answer(product: ProductItem | dict[str, Any], original_answer: str) -> str:
    title = _product_field(product, "title") or "the safer catalog candidate"
    facts = _product_facts(product)
    if _contains_cjk(original_answer):
        fact_text = f"，本地目录标注：{'; '.join(facts)}" if facts else ""
        return f"本地目录中更稳妥的推荐是 {title}{fact_text}。"
    fact_text = f"; local catalog indicates {', '.join(facts)}" if facts else ""
    return f"A safer local-catalog recommendation is {title}{fact_text}."


def _product_facts(product: ProductItem | dict[str, Any]) -> list[str]:
    facts: list[str] = []
    price = _product_field(product, "price")
    if price is not None:
        amount = price.amount if hasattr(price, "amount") else price.get("amount")
        currency = price.currency if hasattr(price, "currency") else price.get("currency")
        if amount is not None and currency:
            facts.append(f"price {amount:g} {currency}")
    availability = _product_field(product, "availability")
    if availability:
        facts.append(f"availability {availability}")
    attributes = _product_field(product, "attributes") or {}
    for key in ["noise_cancellation", "battery_life_hours", "laptop_size_inches", "weight_kg"]:
        value = attributes.get(key)
        if value is not None and value != "":
            facts.append(f"{key} {value}")
    return facts[:3]


def _product_field(product: ProductItem | dict[str, Any], field: str) -> Any:
    if isinstance(product, ProductItem):
        return getattr(product, field)
    return product.get(field)


def _append_repair_note(answer: str, original_answer: str) -> str:
    if "本地目录" in answer or "local catalog" in answer:
        return answer
    if _contains_cjk(original_answer):
        return f"{answer}（已根据本地目录核验并修正未通过核验的声明。）"
    return f"{answer} Local catalog verification was used to correct unsupported claims."


def _qualified_answer(answer: str) -> str:
    if _contains_cjk(answer):
        return f"{answer} 请注意：该回答未能完全通过本地目录核验，建议仅作为待确认候选。"
    return (
        f"{answer} Note: this answer did not fully pass local catalog verification; "
        "treat it as a candidate that needs confirmation."
    )


def _append_fact_note(answer: str, fact: str) -> str:
    return f"{answer} Local catalog indicates {fact}."


def _issue_warning(issue: Any) -> str:
    message = _field(issue, "message")
    if message:
        return str(message)
    return f"Could not deterministically repair {_field(issue, 'claim_type') or 'claim'}."


def _number_text(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{value:g}"
    return str(value)


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in text)


def _field(item: Any, name: str) -> Any:
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)
