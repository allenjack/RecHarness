from recharness import RecHarness, RuleBasedPreferenceParser


def test_headphones_mandatory_anc_and_wired_constraints():
    need = RuleBasedPreferenceParser().parse("Must have ANC and must be wired headphones")

    assert any(
        constraint.field == "attributes.noise_cancellation"
        and constraint.value == "anc"
        for constraint in need.hard_constraints
    )
    assert any(
        constraint.field == "attributes.connection"
        and constraint.value == "wired"
        for constraint in need.hard_constraints
    )


def test_headphones_adapter_enriches_calls_tws_and_workout_terms():
    parser = RuleBasedPreferenceParser()

    calls = parser.parse("Need office calls headphones with microphone noise reduction")
    chinese_calls = parser.parse("需要办公通话和麦克风降噪的头戴耳机")
    true_wireless = parser.parse("Need true wireless TWS earbuds")
    workout = parser.parse("Need gym workout earbuds for 健身")
    usb_c = parser.parse("Need USB-C wired headphones")

    for need in [calls, chinese_calls]:
        assert "office" in need.scenario
        assert any(
            preference.field == "attributes.use_cases"
            and preference.value == "calls"
            for preference in need.soft_preferences
        )
    assert any(
        preference.field == "attributes.connection" and preference.value == "wireless"
        for preference in true_wireless.soft_preferences
    )
    assert any(
        preference.field == "attributes.water_resistance"
        and preference.value == "sweat_resistant"
        for preference in workout.soft_preferences
    )
    assert any(
        preference.field == "attributes.connection" and preference.value == "wired"
        for preference in usb_c.soft_preferences
    )


def test_headphones_claim_checks_detect_common_overclaims():
    harness = RecHarness.from_jsonl_catalog("examples/headphones/catalog.jsonl")
    report = harness.verify_agent_recommendation(
        "Find wireless headphones under 1000 RMB",
        (
            "I recommend SonicLite AirBuds. It costs 699 RMB, has active noise cancellation, "
            "low latency, 30 hours battery, and is sweat resistant."
        ),
    )

    claim_types = {issue.claim_type for issue in report.claim_issues}
    assert {"noise_cancellation", "latency", "battery_life", "water_resistance"} <= claim_types
    assert report.status == "warning"


def test_headphones_connection_mismatch_is_hard_claim_issue():
    harness = RecHarness.from_jsonl_catalog("examples/headphones/catalog.jsonl")
    report = harness.verify_agent_recommendation(
        "Find wireless headphones under 1000 RMB",
        "I recommend BudgetTune Wired 50. It costs 199 RMB and is wireless.",
    )

    assert report.status == "fail"
    assert any(issue.claim_type == "connection" for issue in report.claim_issues)


def test_headphones_product_name_substrings_do_not_create_connection_claims():
    harness = RecHarness.from_jsonl_catalog("examples/headphones/catalog.jsonl")
    report = harness.verify_agent_recommendation(
        "Find headphones under 1000 RMB",
        "I recommend FocusBean ANC Clip. It costs 999 RMB.",
    )

    assert report.status == "pass"
    assert not any(issue.claim_type == "connection" for issue in report.claim_issues)


def test_headphones_assist_prefers_relevant_anc_commute_products():
    harness = RecHarness.from_jsonl_catalog("examples/headphones/catalog.jsonl")
    bundle = harness.assist("想找1000元以内，适合通勤，有降噪的蓝牙耳机", top_k=3)

    recommended_ids = [candidate.product.product_id for candidate in bundle.recommended]
    assert "hp_009" in recommended_ids or "hp_013" in recommended_ids
    assert all(candidate.violations == [] for candidate in bundle.recommended)
