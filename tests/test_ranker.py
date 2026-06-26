from recharness import JsonlCatalog, RuleBasedPreferenceParser, ScoredProduct, SimpleRanker


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
