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


def test_parser_extracts_waterproof_and_water_resistant_preferences():
    parser = RuleBasedPreferenceParser()

    mandatory = parser.parse("Find a backpack that must be waterproof")
    chinese_mandatory = parser.parse("必须防水的通勤双肩包")
    water_resistant = parser.parse("Find a water-resistant backpack")
    chinese_splash = parser.parse("想要防泼水的双肩包")

    assert any(
        constraint.field == "attributes.water_resistance"
        and constraint.operator == "contains"
        and constraint.value == "waterproof"
        for constraint in mandatory.hard_constraints
    )
    assert any(
        constraint.field == "attributes.water_resistance"
        and constraint.value == "waterproof"
        for constraint in chinese_mandatory.hard_constraints
    )
    assert any(
        preference.field == "attributes.water_resistance"
        and preference.value == "water_resistant"
        and preference.polarity == "positive"
        for preference in water_resistant.soft_preferences
    )
    assert any(
        preference.field == "attributes.water_resistance"
        and preference.value == "water_resistant"
        for preference in chinese_splash.soft_preferences
    )


def test_parser_extracts_weight_constraints_and_preferences():
    parser = RuleBasedPreferenceParser()

    english_numeric = parser.parse("Find a backpack under 1kg")
    chinese_numeric = parser.parse("1kg以下的轻量双肩包")
    lightweight = parser.parse("Find a lightweight backpack")
    not_heavy = parser.parse("不要太重的通勤双肩包")

    assert any(
        constraint.field == "attributes.weight_kg"
        and constraint.operator == "<="
        and constraint.value == 1
        and constraint.unit == "kg"
        for constraint in english_numeric.hard_constraints
    )
    assert any(
        constraint.field == "attributes.weight_kg"
        and constraint.value == 1
        for constraint in chinese_numeric.hard_constraints
    )
    assert any(
        preference.field == "attributes.weight_kg"
        and preference.value == "lightweight"
        for preference in lightweight.soft_preferences
    )
    assert any(
        preference.field == "attributes.weight_kg"
        and preference.value == "heavy"
        and preference.polarity == "negative"
        for preference in not_heavy.negative_preferences
    )


def test_parser_extracts_ultralight_as_distinct_weight_preference():
    parser = RuleBasedPreferenceParser()

    english = parser.parse("Find an ultralight backpack")
    chinese = parser.parse("想要超轻双肩包")

    assert any(
        preference.field == "attributes.weight_kg"
        and preference.value == "ultralight"
        and preference.weight == 0.85
        for preference in english.soft_preferences
    )
    assert any(
        preference.field == "attributes.weight_kg"
        and preference.value == "ultralight"
        and preference.weight == 0.85
        for preference in chinese.soft_preferences
    )


def test_parser_extracts_capacity_constraints_and_preferences():
    parser = RuleBasedPreferenceParser()

    lower_bound = parser.parse("Find a backpack with at least 30L capacity")
    approximate = parser.parse("Find a backpack around 20L")
    chinese_approximate = parser.parse("约20升的通勤双肩包")

    assert any(
        constraint.field == "attributes.capacity_liters"
        and constraint.operator == ">="
        and constraint.value == 30
        and constraint.unit == "L"
        for constraint in lower_bound.hard_constraints
    )
    assert any(
        preference.field == "attributes.capacity_liters"
        and preference.value == 20
        for preference in approximate.soft_preferences
    )
    assert any(
        preference.field == "attributes.capacity_liters"
        and preference.value == 20
        for preference in chinese_approximate.soft_preferences
    )


def test_parser_extracts_new_categories_and_scenarios():
    parser = RuleBasedPreferenceParser()

    assert parser.parse("Bluetooth headphones for office").category == "headphones"
    assert parser.parse("running shoes for hiking").category == "shoes"
    assert parser.parse("mechanical keyboard for gaming").category == "keyboard"
    assert parser.parse("office mouse").category == "mouse"

    need = parser.parse("Need shoes for business trip, hiking, running, gaming, and office")

    assert need.scenario == [
        "business_trip",
        "hiking",
        "running",
        "gaming",
        "office",
    ]
