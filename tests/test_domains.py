from recharness import RuleBasedPreferenceParser
from recharness.domains import get_domain_adapter


def test_no_domain_adapter_keeps_current_behavior():
    need = RuleBasedPreferenceParser().parse("Find a mouse under 500 RMB")

    assert get_domain_adapter("mouse") is None
    assert need.category == "mouse"


def test_headphones_adapter_enriches_chinese_anc_wireless_commute_query():
    need = RuleBasedPreferenceParser().parse("想找1000元以内，适合通勤，有降噪的蓝牙耳机")

    assert need.category == "headphones"
    assert "commute" in need.scenario
    assert any(pref.field == "attributes.connection" for pref in need.soft_preferences)
    assert any(
        pref.field == "attributes.noise_cancellation" and pref.value == "anc"
        for pref in need.soft_preferences
    )


def test_headphones_adapter_adds_low_latency_and_battery_constraints():
    low_latency = RuleBasedPreferenceParser().parse("Need low latency gaming headphones")
    battery = RuleBasedPreferenceParser().parse("Need wireless headphones with at least 30 hours")

    assert "gaming" in low_latency.scenario
    assert any(
        constraint.field == "attributes.latency_ms" and constraint.operator == "<="
        for constraint in low_latency.hard_constraints
    )
    assert any(
        constraint.field == "attributes.battery_life_hours"
        and constraint.operator == ">="
        and constraint.value == 30
        for constraint in battery.hard_constraints
    )


def test_headphones_adapter_adds_sweat_running_preference():
    need = RuleBasedPreferenceParser().parse("需要跑步用、防汗、轻量的耳机")

    assert "running" in need.scenario
    assert any(
        pref.field == "attributes.water_resistance" and pref.value == "sweat_resistant"
        for pref in need.soft_preferences
    )
