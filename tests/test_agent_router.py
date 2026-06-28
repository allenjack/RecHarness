from recharness import AgentHarnessRouter, AssistRequest, ParseRequest, VerifyRequest
from recharness.catalog import CatalogConfig, MultiCatalogConfig


def test_agent_router_routes_by_explicit_domain_and_caches_harnesses():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

    response = router.assist(
        AssistRequest(
            user_query="Find wireless headphones under 1000 RMB for office calls.",
            domain="headphones",
            top_k=2,
        )
    )
    router.assist(AssistRequest(user_query="Find ANC headphones", domain="headphones"))

    assert response.status == "warning"
    assert response.domain == "headphones"
    assert response.bundle is not None
    assert all(
        candidate.product.category == "headphones"
        for candidate in response.bundle.recommended
    )
    assert list(router._harness_cache) == [("headphones", "full")]


def test_agent_router_assist_status_ok_without_diagnostics():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

    response = router.assist(
        AssistRequest(user_query="Find headphones", domain="headphones", top_k=2)
    )

    assert response.status == "ok"
    assert response.warnings == []
    assert response.bundle is not None
    assert response.bundle.rejected == []


def test_agent_router_routes_by_parsed_category_and_default_fallback():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

    parsed = router.parse(ParseRequest(user_query="想找1000元以内，有降噪的蓝牙耳机"))
    fallback = router.assist(AssistRequest(user_query="Something under 1000 RMB", top_k=1))

    assert parsed.status == "ok"
    assert parsed.domain == "headphones"
    assert parsed.user_need is not None
    assert parsed.user_need.category == "headphones"
    assert fallback.status == "warning"
    assert fallback.domain == "backpacks"


def test_agent_router_unknown_domain_and_no_route_return_error_envelopes():
    no_default = AgentHarnessRouter(
        MultiCatalogConfig(
            catalogs={
                "headphones": CatalogConfig(
                    path="examples/headphones/catalog.jsonl",
                    category="headphones",
                )
            }
        )
    )

    unknown = no_default.assist(AssistRequest(user_query="Find something", domain="shoes"))
    no_route = no_default.assist(AssistRequest(user_query="Find something", top_k=1))

    assert unknown.status == "error"
    assert unknown.errors == ["Unknown domain: shoes"]
    assert no_route.status == "error"
    assert "No catalog route" in no_route.errors[0]


def test_agent_router_caches_harnesses_by_domain_and_variant():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

    router.assist(AssistRequest(user_query="Find headphones", domain="headphones"))
    full_first = router._harness_cache[("headphones", "full")]
    router.assist(AssistRequest(user_query="Find ANC headphones", domain="headphones"))
    full_second = router._harness_cache[("headphones", "full")]

    router.assist(
        AssistRequest(
            user_query="Find headphones",
            domain="headphones",
            variant="keyword_only",
        )
    )
    keyword_first = router._harness_cache[("headphones", "keyword_only")]
    router.assist(
        AssistRequest(
            user_query="Find ANC headphones",
            domain="headphones",
            variant="keyword_only",
        )
    )
    keyword_second = router._harness_cache[("headphones", "keyword_only")]

    assert full_first is full_second
    assert keyword_first is keyword_second
    assert full_first is not keyword_first
    assert sorted(router._harness_cache) == [
        ("headphones", "full"),
        ("headphones", "keyword_only"),
    ]


def test_agent_router_unknown_variant_returns_error_envelope():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

    response = router.assist(
        AssistRequest(
            user_query="Find headphones",
            domain="headphones",
            variant="unknown",
        )
    )

    assert response.status == "error"
    assert "Unknown harness variant" in response.errors[0]


def test_agent_router_verify_uses_stable_error_and_detects_overclaim():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

    response = router.verify(
        VerifyRequest(
            user_query="想找1000元以内，适合通勤，有降噪的蓝牙耳机",
            domain="headphones",
            agent_answer="我推荐 SonicLite AirBuds，售价699元，有主动降噪。",
        )
    )

    assert response.status == "warning"
    assert response.report is not None
    assert response.report.overstated_claims
    assert response.report.claim_issues[0].claim_type == "noise_cancellation"
