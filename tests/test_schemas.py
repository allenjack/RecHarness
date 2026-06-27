from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from recharness import (
    ClaimIssue,
    Constraint,
    Evidence,
    Money,
    Preference,
    ProductItem,
    RecommendationBundle,
    RecommendationCandidate,
    TraceEvent,
    UserNeed,
    VerificationReport,
)


def test_product_item_accepts_generic_attributes_and_serializes_nested_models():
    product = ProductItem(
        product_id="bag_001",
        title="UrbanLite Commuter Backpack 22L",
        category="backpack",
        brand="UrbanLite",
        price=Money(amount=899, currency="CNY"),
        attributes={"laptop_size_inches": 14, "style": ["minimal", "casual"]},
        evidence=[
            Evidence(
                field="attributes.laptop_size_inches",
                value=14,
                source_type="manufacturer_spec",
            )
        ],
    )

    dumped = product.model_dump()

    assert dumped["price"] == {"amount": 899.0, "currency": "CNY"}
    assert dumped["attributes"]["style"] == ["minimal", "casual"]
    assert dumped["evidence"][0]["field"] == "attributes.laptop_size_inches"


def test_money_rejects_negative_amounts():
    with pytest.raises(ValidationError):
        Money(amount=-1, currency="USD")


def test_constraint_supports_dot_path_fields():
    constraint = Constraint(
        field="price.amount",
        operator="<=",
        value=1500,
        severity="hard",
        source="user",
    )

    assert constraint.field == "price.amount"
    assert constraint.operator == "<="


def test_preference_defaults_to_positive_polarity():
    preference = Preference(field="attributes.weight_kg", value="lightweight")

    assert preference.polarity == "positive"


def test_verification_report_serializes_research_fields():
    product = ProductItem(
        product_id="bag_001",
        title="UrbanLite Commuter Backpack 22L",
        category="backpack",
    )
    issue = ClaimIssue(
        product_id="bag_001",
        product_title="UrbanLite Commuter Backpack 22L",
        claim_type="price",
        issue_type="incorrect",
        severity="hard",
        field="price.amount",
        claimed_value=699,
        observed_value=899,
        message="Price mismatch.",
    )

    report = VerificationReport(
        user_need=UserNeed(raw_query="Find a commuting backpack"),
        mentioned_products=["UrbanLite Commuter Backpack 22L"],
        resolved_products=[product],
        unresolved_mentions=["PhantomPack Air 25L"],
        product_grounded=True,
        claim_issues=[issue],
    )

    dumped = report.model_dump()

    assert dumped["product_grounded"] is True
    assert dumped["resolved_products"][0]["product_id"] == "bag_001"
    assert dumped["unresolved_mentions"] == ["PhantomPack Air 25L"]
    assert dumped["claim_issues"][0]["product_id"] == "bag_001"
    assert dumped["claim_issues"][0]["issue_type"] == "incorrect"


def test_recommendation_bundle_requires_a_trace_id():
    need = UserNeed(raw_query="Find a commuting backpack under 1500 RMB")
    product = ProductItem(
        product_id="bag_001",
        title="UrbanLite Commuter Backpack 22L",
        category="backpack",
    )
    candidate = RecommendationCandidate(product=product, final_score=0.9)

    bundle = RecommendationBundle(
        user_need=need,
        candidates=[candidate],
        recommended=[candidate],
        rejected=[],
        comparison_axes=["price", "laptop fit"],
        summary_for_agent="Recommend UrbanLite as the safest choice.",
        trace_id="trace_001",
    )

    assert bundle.recommended[0].product.product_id == "bag_001"
    assert bundle.trace_id == "trace_001"


def test_trace_event_defaults_timestamp_when_not_supplied():
    event = TraceEvent(
        trace_id="trace_001",
        step=1,
        event_type="catalog_load",
        payload={"path": "examples/backpacks/catalog.jsonl"},
    )

    assert isinstance(event.timestamp, datetime)
    assert event.timestamp.tzinfo == UTC
