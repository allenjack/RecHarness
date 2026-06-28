"""Deterministic rule-based parser for simple shopping needs."""

from __future__ import annotations

import re

from recharness.schema import Constraint, Preference, UserNeed


class RuleBasedPreferenceParser:
    """Extract common shopping constraints without external LLM calls."""

    _price_patterns = [
        re.compile(
            r"(?:under|below|less than)\s*(?:rmb|cny|¥|\$)?\s*"
            r"(\d+(?:\.\d+)?)(?!\s*kg)",
            re.I,
        ),
        re.compile(r"(?:rmb|cny|¥|\$)\s*(\d+(?:\.\d+)?)\s*(?:or less|max|maximum)?", re.I),
        re.compile(
            r"(\d+(?:\.\d+)?)\s*(?:元|块|rmb|cny)\s*"
            r"(?:以内|以下|内|or less|max|maximum)?",
            re.I,
        ),
    ]
    _laptop_patterns = [
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:-| )?\s*inch(?:es)?\s*laptop", re.I),
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:寸|英寸)\s*(?:电脑|笔记本)?", re.I),
    ]
    _weight_patterns = [
        re.compile(r"(?:under|below|less than)\s*(\d+(?:\.\d+)?)\s*kg", re.I),
        re.compile(r"(\d+(?:\.\d+)?)\s*kg\s*(?:以内|以下)"),
        re.compile(r"不超过\s*(\d+(?:\.\d+)?)\s*kg", re.I),
    ]
    _capacity_patterns = [
        re.compile(r"(?:at least|minimum)\s*(\d+(?:\.\d+)?)\s*l", re.I),
        re.compile(r"(?:至少|不少于)\s*(\d+(?:\.\d+)?)\s*(?:l|升)", re.I),
    ]
    _approx_capacity_patterns = [
        re.compile(r"(?:around|about)\s*(\d+(?:\.\d+)?)\s*l", re.I),
        re.compile(r"(?:大约|约)\s*(\d+(?:\.\d+)?)\s*(?:l|升)", re.I),
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:l|升)", re.I),
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

        need.hard_constraints.extend(self._extract_water_resistance_constraints(query))
        need.soft_preferences.extend(self._extract_water_resistance_preferences(query))
        weight_constraint = self._extract_weight_constraint(query)
        if weight_constraint is not None:
            need.hard_constraints.append(weight_constraint)
        need.soft_preferences.extend(self._extract_weight_preferences(query))
        capacity_constraint = self._extract_capacity_constraint(query)
        if capacity_constraint is not None:
            need.hard_constraints.append(capacity_constraint)
        else:
            capacity_preference = self._extract_capacity_preference(query)
            if capacity_preference is not None:
                need.soft_preferences.append(capacity_preference)
        need.negative_preferences.extend(self._extract_negative_preferences(normalized))

        return need

    def _extract_category(self, normalized_query: str) -> str | None:
        category_terms = [
            ("headphones", ["headphones", "earphones", "earbuds", "耳机", "蓝牙耳机"]),
            ("shoes", ["running shoes", "sneakers", "shoes", "运动鞋", "跑鞋", "鞋"]),
            ("keyboard", ["mechanical keyboard", "keyboard", "机械键盘", "键盘"]),
            ("mouse", ["mouse", "鼠标"]),
        ]
        if (
            "backpack" in normalized_query
            or "双肩包" in normalized_query
            or "背包" in normalized_query
        ):
            return "backpack"
        for category, terms in category_terms:
            if any(term in normalized_query for term in terms):
                return category
        return None

    def _extract_scenarios(self, normalized_query: str) -> list[str]:
        scenarios: list[str] = []
        if "commut" in normalized_query or "通勤" in normalized_query:
            scenarios.append("commute")
        if (
            "travel" in normalized_query
            or "旅行" in normalized_query
            or "旅游" in normalized_query
        ):
            scenarios.append("travel")
        if "business trip" in normalized_query or "出差" in normalized_query:
            scenarios.append("business_trip")
        if (
            "hiking" in normalized_query
            or "outdoor" in normalized_query
            or "outdoors" in normalized_query
            or "户外" in normalized_query
            or "徒步" in normalized_query
        ):
            scenarios.append("hiking")
        if "running" in normalized_query or "跑步" in normalized_query:
            scenarios.append("running")
        if "gaming" in normalized_query or "游戏" in normalized_query or "电竞" in normalized_query:
            scenarios.append("gaming")
        if "office" in normalized_query or "办公" in normalized_query:
            scenarios.append("office")
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

    def _extract_water_resistance_constraints(self, query: str) -> list[Constraint]:
        normalized = query.lower()
        mandatory = (
            "must be waterproof" in normalized
            or "fully waterproof required" in normalized
            or "必须防水" in query
            or "一定要防水" in query
        )
        if not mandatory:
            return []
        return [
            Constraint(
                field="attributes.water_resistance",
                operator="contains",
                value="waterproof",
                severity="hard",
                source="user",
            )
        ]

    def _extract_water_resistance_preferences(self, query: str) -> list[Preference]:
        normalized = query.lower()
        preferences: list[Preference] = []
        mandatory = self._extract_water_resistance_constraints(query)
        water_resistant = (
            "water-resistant" in normalized
            or "water resistant" in normalized
            or "splash-resistant" in normalized
            or "splash resistant" in normalized
            or "防泼水" in query
            or "防溅水" in query
        )
        if water_resistant:
            preferences.append(
                Preference(
                    field="attributes.water_resistance",
                    value="water_resistant",
                    weight=0.7,
                    polarity="positive",
                    source="user",
                )
            )
        elif not mandatory and ("waterproof" in normalized or "防水" in query):
            preferences.append(
                Preference(
                    field="attributes.water_resistance",
                    value="waterproof",
                    weight=0.8,
                    polarity="positive",
                    source="user",
                )
            )
        return preferences

    def _extract_weight_constraint(self, query: str) -> Constraint | None:
        for pattern in self._weight_patterns:
            match = pattern.search(query)
            if match:
                return Constraint(
                    field="attributes.weight_kg",
                    operator="<=",
                    value=_number(match.group(1)),
                    unit="kg",
                    severity="hard",
                    source="user",
                )
        return None

    def _extract_weight_preferences(self, query: str) -> list[Preference]:
        normalized = query.lower()
        preferences: list[Preference] = []
        if "ultralight" in normalized or "超轻" in query:
            preferences.append(
                Preference(
                    field="attributes.weight_kg",
                    value="ultralight",
                    weight=0.85,
                    polarity="positive",
                    source="user",
                )
            )
        elif (
            "lightweight" in normalized
            or "light weight" in normalized
            or "轻量" in query
            or "轻便" in query
            or "不重" in query
        ):
            preferences.append(
                Preference(
                    field="attributes.weight_kg",
                    value="lightweight",
                    weight=0.7,
                    polarity="positive",
                    source="user",
                )
            )
        return preferences

    def _extract_capacity_constraint(self, query: str) -> Constraint | None:
        for pattern in self._capacity_patterns:
            match = pattern.search(query)
            if match:
                return Constraint(
                    field="attributes.capacity_liters",
                    operator=">=",
                    value=_number(match.group(1)),
                    unit="L",
                    severity="hard",
                    source="user",
                )
        return None

    def _extract_capacity_preference(self, query: str) -> Preference | None:
        for pattern in self._approx_capacity_patterns:
            match = pattern.search(query)
            if match:
                return Preference(
                    field="attributes.capacity_liters",
                    value=_number(match.group(1)),
                    weight=0.5,
                    polarity="positive",
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
                    polarity="negative",
                    source="user",
                )
            )
        if "not too heavy" in normalized_query or "不要太重" in normalized_query:
            preferences.append(
                Preference(
                    field="attributes.weight_kg",
                    value="heavy",
                    weight=0.7,
                    polarity="negative",
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
