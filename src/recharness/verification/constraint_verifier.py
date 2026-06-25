"""Constraint verification against ProductItem records."""

from __future__ import annotations

from typing import Any

from recharness.schema import Constraint, ConstraintCheck, ProductItem, VerificationReport, Violation


class ConstraintVerifier:
    """Evaluate dot-path constraints against product records."""

    def verify_product(
        self,
        product: ProductItem,
        constraints: list[Constraint],
    ) -> VerificationReport:
        checks: list[ConstraintCheck] = []
        violations: list[Violation] = []

        for constraint in constraints:
            observed = _resolve_field(product, constraint.field)
            satisfied = _is_satisfied(observed, constraint)
            message = _message(constraint, observed, satisfied)

            checks.append(
                ConstraintCheck(
                    constraint=constraint,
                    observed_value=observed,
                    satisfied=satisfied,
                    message=message,
                )
            )
            if not satisfied:
                violations.append(
                    Violation(
                        constraint=constraint,
                        observed_value=observed,
                        severity=constraint.severity,
                        message=message,
                    )
                )

        status = "pass"
        if any(violation.severity == "hard" for violation in violations):
            status = "fail"
        elif violations:
            status = "warning"

        return VerificationReport(status=status, checks=checks, violations=violations)


def _resolve_field(product: ProductItem, field: str) -> Any:
    value: Any = product.model_dump()
    for part in field.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
        if value is None:
            return None
    return value


def _is_satisfied(observed: Any, constraint: Constraint) -> bool:
    if constraint.operator == "exists":
        return _has_value(observed)
    if not _has_value(observed):
        return False

    expected = constraint.value
    if constraint.operator == "=":
        return observed == expected
    if constraint.operator == "!=":
        return observed != expected
    if constraint.operator == "<":
        return observed < expected
    if constraint.operator == "<=":
        return observed <= expected
    if constraint.operator == ">":
        return observed > expected
    if constraint.operator == ">=":
        return observed >= expected
    if constraint.operator == "contains":
        return _contains(observed, expected)
    if constraint.operator == "not_contains":
        return not _contains(observed, expected)
    return False


def _contains(observed: Any, expected: Any) -> bool:
    if isinstance(observed, str):
        return str(expected).lower() in observed.lower()
    if isinstance(observed, (list, tuple, set)):
        expected_text = str(expected).lower()
        return any(str(item).lower() == expected_text for item in observed)
    if isinstance(observed, dict):
        return expected in observed
    return False


def _message(constraint: Constraint, observed: Any, satisfied: bool) -> str:
    if satisfied:
        return f"{constraint.field} satisfies {constraint.operator} {constraint.value}"
    if not _has_value(observed):
        return f"{constraint.field} is missing; expected {constraint.operator} {constraint.value}"
    return (
        f"{constraint.field} observed {observed!r} does not satisfy "
        f"{constraint.operator} {constraint.value!r}"
    )


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if value == "":
        return False
    if isinstance(value, (list, dict, set, tuple)) and len(value) == 0:
        return False
    return True
