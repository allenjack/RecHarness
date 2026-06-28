from recharness import (
    JsonlCatalog,
    Money,
    ProductItem,
    RuleBasedPreferenceParser,
    ScoredProduct,
    SimpleRanker,
)


def test_simple_ranker_prefers_constraint_satisfying_non_negative_style_products():
    catalog = JsonlCatalog.load("examples/backpacks/catalog.jsonl")
    need = RuleBasedPreferenceParser().parse(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop "
        "and is not too business"
    )
    retrieved = [
        ScoredProduct(product=catalog[0], score=1.0, matched_terms=["commute", "backpack"]),
        ScoredProduct(product=catalog[1], score=1.0, matched_terms=["commute", "backpack"]),
    ]

    ranked = SimpleRanker().rank(need, retrieved, top_k=3)

    assert ranked[0].product.product_id == "bag_001"
    assert ranked[1].product.product_id == "bag_002"
    assert ranked[0].final_score is not None
    assert ranked[0].violations == []
    assert all(candidate.constraint_score == 1.0 for candidate in ranked)
    assert ranked[0].preference_score > ranked[1].preference_score


def test_simple_ranker_prefers_ultralight_weight_for_ultralight_queries():
    need = RuleBasedPreferenceParser().parse("Find an ultralight backpack")
    products = [
        ProductItem(
            product_id="ultra",
            title="Ultra Pack",
            category="backpack",
            price=Money(amount=100, currency="CNY"),
            attributes={"weight_kg": 0.75},
        ),
        ProductItem(
            product_id="light",
            title="Light Pack",
            category="backpack",
            price=Money(amount=100, currency="CNY"),
            attributes={"weight_kg": 0.95},
        ),
    ]
    retrieved = [ScoredProduct(product=product, score=1.0) for product in products]

    ranked = SimpleRanker().rank(need, retrieved, top_k=2)

    assert ranked[0].product.product_id == "ultra"
    assert ranked[0].preference_score > ranked[1].preference_score


def test_simple_ranker_gives_partial_weight_preference_for_lightweight_and_missing_weight():
    need = RuleBasedPreferenceParser().parse("Find a lightweight backpack")
    products = [
        ProductItem(
            product_id="light",
            title="Light Pack",
            category="backpack",
            attributes={"weight_kg": 0.95},
        ),
        ProductItem(
            product_id="missing",
            title="Missing Weight Pack",
            category="backpack",
            attributes={},
        ),
        ProductItem(
            product_id="heavy",
            title="Heavy Pack",
            category="backpack",
            attributes={"weight_kg": 1.4},
        ),
    ]
    retrieved = [ScoredProduct(product=product, score=1.0) for product in products]

    ranked = SimpleRanker().rank(need, retrieved, top_k=3)
    by_id = {candidate.product.product_id: candidate for candidate in ranked}

    assert by_id["light"].preference_score == 1.0
    assert 0 < by_id["missing"].preference_score < by_id["light"].preference_score
    assert by_id["missing"].preference_score > by_id["heavy"].preference_score
