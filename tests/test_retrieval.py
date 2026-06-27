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


def test_attribute_filter_retriever_keeps_hard_constraint_violations_for_diagnosis():
    catalog = JsonlCatalog.load("examples/backpacks/catalog.jsonl")
    need = RuleBasedPreferenceParser().parse(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop"
    )

    results = AttributeFilterRetriever().retrieve(need, catalog, top_k=len(catalog))
    product_ids = [result.product.product_id for result in results]
    scores = {result.product.product_id: result.score for result in results}

    assert "bag_001" in product_ids
    assert "bag_002" in product_ids
    assert "bag_003" in product_ids
    assert "bag_004" in product_ids
    assert scores["bag_001"] > scores["bag_003"]
    assert scores["bag_001"] > scores["bag_004"]


def test_hybrid_retriever_keeps_invalid_products_below_valid_products():
    catalog = JsonlCatalog.load("examples/backpacks/catalog.jsonl")
    need = RuleBasedPreferenceParser().parse(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop"
    )

    results = HybridRetriever().retrieve(need, catalog, top_k=len(catalog))
    product_ids = [result.product.product_id for result in results]

    assert "bag_003" in product_ids
    assert "bag_004" in product_ids
    assert product_ids.index("bag_001") < product_ids.index("bag_003")
    assert product_ids.index("bag_001") < product_ids.index("bag_004")
