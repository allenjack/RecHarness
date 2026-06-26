from recharness import (
    AttributeFilterRetriever,
    HybridRetriever,
    JsonlCatalog,
    KeywordRetriever,
    RuleBasedPreferenceParser,
)


def test_keyword_retriever_scores_matching_products_from_need_text():
    catalog = JsonlCatalog.load("examples/backpacks/catalog.jsonl")
    need = RuleBasedPreferenceParser().parse("Find a commuting backpack")

    results = KeywordRetriever().retrieve(need, catalog, top_k=2)

    assert len(results) == 2
    assert results[0].product.product_id == "bag_001"
    assert results[0].score > 0
    assert "commute" in results[0].matched_terms


def test_attribute_filter_retriever_removes_hard_constraint_violations():
    catalog = JsonlCatalog.load("examples/backpacks/catalog.jsonl")
    need = RuleBasedPreferenceParser().parse(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop"
    )

    results = AttributeFilterRetriever().retrieve(need, catalog, top_k=10)
    product_ids = [result.product.product_id for result in results]

    assert "bag_001" in product_ids
    assert "bag_002" in product_ids
    assert "bag_003" not in product_ids
    assert "bag_004" not in product_ids


def test_hybrid_retriever_returns_keyword_ranked_products_that_pass_constraints():
    catalog = JsonlCatalog.load("examples/backpacks/catalog.jsonl")
    need = RuleBasedPreferenceParser().parse(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop"
    )

    results = HybridRetriever().retrieve(need, catalog, top_k=3)

    assert len(results) == 3
    assert all(result.product.price.amount <= 1500 for result in results)
    assert all(result.product.attributes["laptop_size_inches"] >= 14 for result in results)
