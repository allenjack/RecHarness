from recharness import ClaimVerifier, Money, ProductItem


def make_product(**overrides):
    data = {
        "product_id": "bag_test",
        "title": "Test Pack",
        "category": "backpack",
        "price": Money(amount=1299, currency="CNY"),
        "availability": "out_of_stock",
        "attributes": {
            "laptop_size_inches": 14,
            "weight_kg": 1.25,
            "water_resistance": "splash_resistant",
        },
    }
    data.update(overrides)
    return ProductItem(**data)


def test_claim_verifier_returns_structured_waterproof_issue_and_compat_string():
    issues = ClaimVerifier().verify_claims(
        make_product(),
        "Test Pack is fully waterproof.",
    )

    assert issues[0].claim_type == "water_resistance"
    assert issues[0].severity == "warning"
    assert issues[0].field == "attributes.water_resistance"
    assert issues[0].claimed_value == "waterproof"
    assert issues[0].observed_value == "splash_resistant"
    assert "waterproof" in issues[0].message


def test_claim_verifier_detects_price_mismatch_as_hard_issue():
    issues = ClaimVerifier().verify_claims(
        make_product(),
        "Test Pack costs 999 RMB.",
    )

    assert issues[0].claim_type == "price"
    assert issues[0].severity == "hard"
    assert issues[0].field == "price.amount"
    assert issues[0].claimed_value == 999
    assert issues[0].observed_value == 1299


def test_claim_verifier_detects_laptop_fit_overclaim():
    issues = ClaimVerifier().verify_claims(
        make_product(),
        "Test Pack fits a 16-inch laptop.",
    )

    assert issues[0].claim_type == "laptop_fit"
    assert issues[0].severity == "hard"
    assert issues[0].field == "attributes.laptop_size_inches"
    assert issues[0].claimed_value == 16
    assert issues[0].observed_value == 14


def test_claim_verifier_detects_lightweight_overclaim():
    issues = ClaimVerifier().verify_claims(
        make_product(),
        "Test Pack is lightweight and easy to carry.",
    )

    assert issues[0].claim_type == "weight"
    assert issues[0].severity == "warning"
    assert issues[0].field == "attributes.weight_kg"
    assert issues[0].observed_value == 1.25


def test_claim_verifier_detects_availability_overclaim():
    issues = ClaimVerifier().verify_claims(
        make_product(),
        "Test Pack is in stock and available now.",
    )

    assert issues[0].claim_type == "availability"
    assert issues[0].severity == "hard"
    assert issues[0].field == "availability"
    assert issues[0].claimed_value == "in_stock"
    assert issues[0].observed_value == "out_of_stock"


def test_claim_verifier_allows_supported_claims():
    issues = ClaimVerifier().verify_claims(
        make_product(
            price=Money(amount=999, currency="CNY"),
            availability="in_stock",
            attributes={
                "laptop_size_inches": 16,
                "weight_kg": 0.85,
                "water_resistance": "waterproof",
            },
        ),
        "Test Pack costs 999 RMB, is waterproof, fits a 16-inch laptop, "
        "is lightweight, and is in stock.",
    )

    assert issues == []
