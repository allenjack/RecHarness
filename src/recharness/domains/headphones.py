"""Headphones domain adapter."""

from __future__ import annotations

import re
from typing import Any

from recharness.schema import ClaimIssue, Constraint, Preference, ProductItem, UserNeed


class HeadphonesAdapter:
    category = "headphones"

    def enrich_user_need(self, need: UserNeed, query: str) -> UserNeed:
        lowered = query.lower()
        need.category = "headphones"
        _add_use_case_scenarios(need, lowered, query)
        _add_connection_preferences(need, lowered, query)
        _add_noise_cancellation_preferences(need, lowered, query)
        _add_latency_preferences(need, lowered, query)
        _add_battery_preferences(need, lowered, query)
        _add_sweat_preferences(need, lowered, query)
        return need

    def verify_claims(self, product: ProductItem, text: str) -> list[ClaimIssue]:
        lowered = text.lower()
        issues: list[ClaimIssue] = []
        issues.extend(_noise_cancellation_issues(product, lowered))
        issues.extend(_latency_issues(product, lowered))
        issues.extend(_battery_issues(product, text))
        issues.extend(_connection_issues(product, lowered, text))
        issues.extend(_sweat_resistance_issues(product, lowered, text))
        return issues


def _add_use_case_scenarios(need: UserNeed, lowered: str, query: str) -> None:
    mappings = [
        ("office", ["office", "calls", "办公", "通话"]),
        ("commute", ["commute", "commuting", "通勤"]),
        ("travel", ["travel", "旅行"]),
        ("running", ["running", "跑步", "运动"]),
        ("gaming", ["gaming", "game", "游戏", "电竞"]),
        ("study", ["study", "学习"]),
        ("studio", ["studio", "music", "录音", "音乐"]),
    ]
    for scenario, terms in mappings:
        if any(term in lowered or term in query for term in terms):
            _append_unique(need.scenario, scenario)


def _add_connection_preferences(need: UserNeed, lowered: str, query: str) -> None:
    wireless = any(
        term in lowered or term in query
        for term in ["wireless", "bluetooth", "蓝牙", "无线"]
    )
    wired = any(term in lowered or term in query for term in ["wired", "usb", "有线"])
    if wireless:
        if any(
            term in lowered or term in query
            for term in ["must be wireless", "必须无线", "必须蓝牙"]
        ):
            _append_constraint(need, "attributes.connection", "contains", "wireless")
        else:
            _append_preference(need, "attributes.connection", "wireless", 0.7)
    if wired:
        if any(term in lowered or term in query for term in ["must be wired", "必须有线"]):
            _append_constraint(need, "attributes.connection", "contains", "wired")
        else:
            _append_preference(need, "attributes.connection", "wired", 0.6)


def _add_noise_cancellation_preferences(need: UserNeed, lowered: str, query: str) -> None:
    if not _mentions_anc(lowered, query):
        return
    if any(
        term in lowered or term in query
        for term in ["must have anc", "必须降噪", "一定要降噪"]
    ):
        _append_constraint(need, "attributes.noise_cancellation", "=", "anc")
    else:
        _append_preference(need, "attributes.noise_cancellation", "anc", 0.8)


def _add_latency_preferences(need: UserNeed, lowered: str, query: str) -> None:
    explicit = "low latency" in lowered or "低延迟" in query
    gaming = "gaming" in need.scenario
    if explicit:
        _append_constraint(need, "attributes.latency_ms", "<=", 50, unit="ms")
    elif gaming:
        _append_preference(need, "attributes.latency_ms", "low_latency", 0.7)


def _add_battery_preferences(need: UserNeed, lowered: str, query: str) -> None:
    for pattern in [
        re.compile(r"(?:at least|minimum)\s*(\d+(?:\.\d+)?)\s*(?:hours?|h)", re.I),
        re.compile(r"(\d+(?:\.\d+)?)\s*h\+?", re.I),
        re.compile(r"(?:至少)?\s*(\d+(?:\.\d+)?)\s*小时(?:以上)?"),
    ]:
        match = pattern.search(query)
        if match:
            _append_constraint(
                need,
                "attributes.battery_life_hours",
                ">=",
                _number(match.group(1)),
                unit="hours",
            )
            return
    if "long battery life" in lowered or "长续航" in query:
        _append_preference(need, "attributes.battery_life_hours", "long_battery", 0.6)


def _add_sweat_preferences(need: UserNeed, lowered: str, query: str) -> None:
    if any(
        term in lowered or term in query
        for term in ["sweat resistant", "sweatproof", "防汗", "running", "跑步", "运动"]
    ):
        _append_preference(need, "attributes.water_resistance", "sweat_resistant", 0.7)


def _noise_cancellation_issues(product: ProductItem, lowered: str) -> list[ClaimIssue]:
    if not _mentions_anc(lowered, lowered):
        return []
    observed = str(product.attributes.get("noise_cancellation", "unknown"))
    if observed.lower() == "anc":
        return []
    return [
        _issue(
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


def _latency_issues(product: ProductItem, lowered: str) -> list[ClaimIssue]:
    if "low latency" not in lowered and "低延迟" not in lowered:
        return []
    observed = product.attributes.get("latency_ms")
    if observed is None or float(observed) <= 60:
        return []
    return [
        _issue(
            product,
            claim_type="latency",
            issue_type="overstated",
            severity="warning",
            field="attributes.latency_ms",
            claimed_value="low_latency",
            observed_value=observed,
            message=(
                f"{product.title}: low latency claim is overstated; "
                f"catalog latency_ms={observed}"
            ),
        )
    ]


def _battery_issues(product: ProductItem, text: str) -> list[ClaimIssue]:
    claimed_values: list[int | float] = []
    for pattern in [
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours?|h)", re.I),
        re.compile(r"(\d+(?:\.\d+)?)\s*小时"),
    ]:
        claimed_values.extend(_number(match) for match in pattern.findall(text))
    if not claimed_values:
        return []
    observed = product.attributes.get("battery_life_hours")
    if observed is None:
        return []
    issues: list[ClaimIssue] = []
    for claimed in claimed_values:
        if float(claimed) > float(observed):
            severity = "hard" if float(claimed) - float(observed) >= 12 else "warning"
            issues.append(
                _issue(
                    product,
                    claim_type="battery_life",
                    issue_type="incorrect",
                    severity=severity,
                    field="attributes.battery_life_hours",
                    claimed_value=claimed,
                    observed_value=observed,
                    message=(
                        f"{product.title}: battery claim {claimed}h exceeds "
                        f"catalog battery_life_hours={observed}"
                    ),
                )
            )
    return issues


def _connection_issues(product: ProductItem, lowered: str, text: str) -> list[ClaimIssue]:
    observed = str(product.attributes.get("connection", "unknown"))
    claims_wireless = _contains_connection_term(
        lowered,
        text,
        english_terms=["wireless", "bluetooth"],
        exact_terms=["蓝牙", "无线"],
    )
    claims_wired = _contains_connection_term(
        lowered,
        text,
        english_terms=["wired", "usb"],
        exact_terms=["有线"],
    )
    issues: list[ClaimIssue] = []
    if claims_wireless and "wireless" not in observed.lower():
        issues.append(_connection_issue(product, "wireless", observed))
    if claims_wired and "wired" not in observed.lower() and "usb" not in observed.lower():
        issues.append(_connection_issue(product, "wired", observed))
    return issues


def _contains_connection_term(
    lowered: str,
    text: str,
    english_terms: list[str],
    exact_terms: list[str],
) -> bool:
    return any(_contains_ascii_token(lowered, term) for term in english_terms) or any(
        term in text for term in exact_terms
    )


def _contains_ascii_token(lowered: str, term: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered) is not None


def _connection_issue(product: ProductItem, claimed: str, observed: str) -> ClaimIssue:
    return _issue(
        product,
        claim_type="connection",
        issue_type="incorrect",
        severity="hard",
        field="attributes.connection",
        claimed_value=claimed,
        observed_value=observed,
        message=(
            f"{product.title}: connection claim {claimed} conflicts with "
            f"catalog connection={observed}"
        ),
    )


def _sweat_resistance_issues(product: ProductItem, lowered: str, text: str) -> list[ClaimIssue]:
    if not any(
        term in lowered or term in text
        for term in ["sweat resistant", "sweatproof", "防汗"]
    ):
        return []
    observed = str(product.attributes.get("water_resistance", "unknown"))
    if observed.lower() == "sweat_resistant":
        return []
    return [
        _issue(
            product,
            claim_type="water_resistance",
            issue_type="overstated",
            severity="warning",
            field="attributes.water_resistance",
            claimed_value="sweat_resistant",
            observed_value=observed,
            message=(
                f"{product.title}: sweat resistance claim is overstated; "
                f"catalog water_resistance={observed}"
            ),
        )
    ]


def _mentions_anc(lowered: str, query: str) -> bool:
    return any(
        term in lowered or term in query
        for term in [
            "anc",
            "active noise cancellation",
            "active noise cancelling",
            "noise cancellation",
            "noise cancelling",
            "降噪",
            "主动降噪",
        ]
    )


def _append_constraint(
    need: UserNeed,
    field: str,
    operator: str,
    value: Any,
    unit: str | None = None,
) -> None:
    if any(
        constraint.field == field and constraint.operator == operator and constraint.value == value
        for constraint in need.hard_constraints
    ):
        return
    need.hard_constraints.append(
        Constraint(
            field=field,
            operator=operator,  # type: ignore[arg-type]
            value=value,
            unit=unit,
            severity="hard",
            source="user",
        )
    )


def _append_preference(need: UserNeed, field: str, value: Any, weight: float) -> None:
    if any(pref.field == field and pref.value == value for pref in need.soft_preferences):
        return
    need.soft_preferences.append(
        Preference(
            field=field,
            value=value,
            weight=weight,
            polarity="positive",
            source="user",
        )
    )


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _issue(product: ProductItem, **kwargs: Any) -> ClaimIssue:
    return ClaimIssue(product_id=product.product_id, product_title=product.title, **kwargs)


def _number(value: str) -> int | float:
    parsed = float(value)
    if parsed.is_integer():
        return int(parsed)
    return parsed
