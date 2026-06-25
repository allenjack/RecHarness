from recharness import RuleBasedPreferenceParser


def test_parser_extracts_english_budget_category_laptop_size_and_negative_style():
    parser = RuleBasedPreferenceParser()

    need = parser.parse(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop "
        "and is not too business."
    )

    assert need.category == "backpack"
    assert "commute" in need.scenario
    assert any(
        constraint.field == "price.amount"
        and constraint.operator == "<="
        and constraint.value == 1500
        and constraint.unit == "CNY"
        for constraint in need.hard_constraints
    )
    assert any(
        constraint.field == "attributes.laptop_size_inches"
        and constraint.operator == ">="
        and constraint.value == 14
        for constraint in need.hard_constraints
    )
    assert any(
        preference.field == "attributes.style"
        and preference.value == "business"
        for preference in need.negative_preferences
    )


def test_parser_extracts_chinese_budget_laptop_size_and_negative_style():
    parser = RuleBasedPreferenceParser()

    need = parser.parse("1500元以内，适合通勤，能放14寸电脑，不要太商务的双肩包")

    assert need.category == "backpack"
    assert "commute" in need.scenario
    assert any(
        constraint.field == "price.amount"
        and constraint.operator == "<="
        and constraint.value == 1500
        and constraint.unit == "CNY"
        for constraint in need.hard_constraints
    )
    assert any(
        constraint.field == "attributes.laptop_size_inches"
        and constraint.operator == ">="
        and constraint.value == 14
        for constraint in need.hard_constraints
    )
    assert any(
        preference.field == "attributes.style"
        and preference.value == "business"
        for preference in need.negative_preferences
    )


def test_parser_marks_budget_missing_for_shopping_queries_without_price():
    parser = RuleBasedPreferenceParser()

    need = parser.parse("Find a lightweight backpack for commuting")

    assert "budget" in need.missing_slots
