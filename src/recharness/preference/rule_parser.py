"""Deterministic rule-based parser for simple shopping needs."""

from __future__ import annotations

import re

from recharness.schema import Constraint, Preference, UserNeed


class RuleBasedPreferenceParser:
    """Extract common shopping constraints without external LLM calls."""

    _price_patterns = [
        re.compile(r"(?:under|below|less than)\s*(?:rmb|cny|¥|\$)?\s*(\d+(?:\.\d+)?)", re.I),
        re.compile(r"(?:rmb|cny|¥|\$)\s*(\d+(?:\.\d+)?)\s*(?:or less|max|maximum)?", re.I),
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:元|块|rmb|cny)\s*(?:以内|以下|内|or less|max|maximum)?", re.I),
    ]
    _laptop_patterns = [
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:-| )?\s*inch(?:es)?\s*laptop", re.I),
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:寸|英寸)\s*(?:电脑|笔记本)?", re.I),
    ]

    def parse(self, query: str) -> UserNeed:
        normalized = query.lower()
        need = UserNeed(raw_query=query)

        need.category = self._extract_category(normalized)
        need.scenario = self._extract_scenarios(normalized)

        price_constraint = self._extract_price_constraint(query)
        if price_constraint is not None:
            need.hard_constraints.append(price_constraint)
        elif need.category is not None:
            need.missing_slots.append("budget")

        laptop_constraint = self._extract_laptop_constraint(query)
        if laptop_constraint is not None:
            need.hard_constraints.append(laptop_constraint)

        need.negative_preferences.extend(self._extract_negative_preferences(normalized))

        return need

    def _extract_category(self, normalized_query: str) -> str | None:
        if "backpack" in normalized_query or "双肩包" in normalized_query or "背包" in normalized_query:
            return "backpack"
        return None

    def _extract_scenarios(self, normalized_query: str) -> list[str]:
        scenarios: list[str] = []
        if "commut" in normalized_query or "通勤" in normalized_query:
            scenarios.append("commute")
        if "travel" in normalized_query or "旅行" in normalized_query:
            scenarios.append("travel")
        return scenarios

    def _extract_price_constraint(self, query: str) -> Constraint | None:
        for pattern in self._price_patterns:
            match = pattern.search(query)
            if match:
                unit = self._infer_currency(query)
                return Constraint(
                    field="price.amount",
                    operator="<=",
                    value=_number(match.group(1)),
                    unit=unit,
                    severity="hard",
                    source="user",
                )
        return None

    def _extract_laptop_constraint(self, query: str) -> Constraint | None:
        for pattern in self._laptop_patterns:
            match = pattern.search(query)
            if match:
                return Constraint(
                    field="attributes.laptop_size_inches",
                    operator=">=",
                    value=_number(match.group(1)),
                    unit="inch",
                    severity="hard",
                    source="user",
                )
        return None

    def _extract_negative_preferences(self, normalized_query: str) -> list[Preference]:
        preferences: list[Preference] = []
        if (
            "not too business" in normalized_query
            or "not business" in normalized_query
            or "avoid business" in normalized_query
            or "不要太商务" in normalized_query
            or "不要商务" in normalized_query
        ):
            preferences.append(
                Preference(
                    field="attributes.style",
                    value="business",
                    weight=0.8,
                    source="user",
                )
            )
        return preferences

    def _infer_currency(self, query: str) -> str | None:
        lowered = query.lower()
        if "元" in query or "rmb" in lowered or "cny" in lowered or "¥" in query:
            return "CNY"
        if "$" in query or "usd" in lowered:
            return "USD"
        return None


def _number(value: str) -> int | float:
    parsed = float(value)
    if parsed.is_integer():
        return int(parsed)
    return parsed
