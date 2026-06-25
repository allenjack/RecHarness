from recharness import Constraint, ConstraintVerifier, Money, ProductItem


def test_verifier_passes_numeric_dot_path_constraints():
    product = ProductItem(
        product_id="bag_001",
        title="UrbanLite",
        category="backpack",
        price=Money(amount=899, currency="CNY"),
        attributes={"laptop_size_inches": 14, "style": ["minimal", "casual"]},
    )
    verifier = ConstraintVerifier()

    report = verifier.verify_product(
        product,
        [
            Constraint(field="price.amount", operator="<=", value=1500),
            Constraint(field="attributes.laptop_size_inches", operator=">=", value=14),
        ],
    )

    assert report.status == "pass"
    assert len(report.checks) == 2
    assert report.violations == []


def test_verifier_reports_hard_numeric_violation_with_observed_value():
    product = ProductItem(
        product_id="bag_003",
        title="RainGuard Metro Pack",
        category="backpack",
        price=Money(amount=1599, currency="CNY"),
    )
    verifier = ConstraintVerifier()

    report = verifier.verify_product(
        product,
        [Constraint(field="price.amount", operator="<=", value=1500, severity="hard")],
    )

    assert report.status == "fail"
    assert len(report.violations) == 1
    assert report.violations[0].observed_value == 1599
    assert "price.amount" in report.violations[0].message


def test_verifier_supports_contains_not_contains_and_exists():
    product = ProductItem(
        product_id="bag_001",
        title="UrbanLite",
        category="backpack",
        attributes={
            "style": ["minimal", "casual"],
            "water_resistance": "water_resistant",
        },
    )
    verifier = ConstraintVerifier()

    report = verifier.verify_product(
        product,
        [
            Constraint(field="attributes.style", operator="not_contains", value="business"),
            Constraint(field="attributes.water_resistance", operator="contains", value="water"),
            Constraint(field="attributes.style", operator="exists"),
        ],
    )

    assert report.status == "pass"
    assert all(check.satisfied for check in report.checks)


def test_verifier_reports_missing_field_as_violation():
    product = ProductItem(
        product_id="bag_004",
        title="FlexTrail",
        category="backpack",
        attributes={"laptop_size_inches": 13},
    )
    verifier = ConstraintVerifier()

    report = verifier.verify_product(
        product,
        [Constraint(field="attributes.weight_kg", operator="<=", value=1.0)],
    )

    assert report.status == "fail"
    assert report.violations[0].observed_value is None
    assert "missing" in report.violations[0].message.lower()
