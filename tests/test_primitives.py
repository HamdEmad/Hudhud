"""
Unit tests for Hudhud primitive data structures.
"""

import pytest
from hudhud.primitives import SearchQuery, SearchResult, SearchResponse


def test_search_query_initialization_and_normalization():
    q = SearchQuery(
        text="  STM32F401RE   ",
        limit=15,
        allowed_domains=("https://www.st.com/en", "MOUSER.COM/"),
        excluded_domains=("http://spam.org",),
    )

    assert q.text == "STM32F401RE"
    assert q.limit == 15
    assert q.allowed_domains == ("st.com", "mouser.com")
    assert q.excluded_domains == ("spam.org",)


def test_search_query_validation():
    with pytest.raises(ValueError, match="cannot be empty"):
        SearchQuery(text="")

    with pytest.raises(ValueError, match="limit must be at least 1"):
        SearchQuery(text="test", limit=0)

    with pytest.raises(ValueError, match="timeout_seconds must be positive"):
        SearchQuery(text="test", timeout_seconds=-1)


def test_domain_rules_matching():
    q = SearchQuery(
        text="amplifier",
        allowed_domains=("ti.com", "analog.com"),
        excluded_domains=("community.ti.com",),
    )

    # Allowed domain
    assert q.matches_domain_rules("https://www.ti.com/product/OPA2134") is True
    assert q.matches_domain_rules("https://ti.com/product/OPA2134") is True
    assert q.matches_domain_rules("https://www.analog.com/ad820") is True

    # Excluded domain (even though ti.com is allowed, community.ti.com is excluded)
    assert q.matches_domain_rules("https://community.ti.com/threads/123") is False

    # Unlisted domain when allowed_domains is present
    assert q.matches_domain_rules("https://www.mouser.com/product") is False


def test_domain_rules_exclusion_only():
    q = SearchQuery(
        text="capacitors",
        excluded_domains=("pinterest.com", "facebook.com"),
    )

    assert q.matches_domain_rules("https://www.murata.com") is True
    assert q.matches_domain_rules("https://pinterest.com/pin/123") is False
    assert q.matches_domain_rules("https://sub.facebook.com/post") is False


def test_search_result_properties():
    r = SearchResult(
        title="TI LM317 Regulator",
        url="https://www.ti.com/lit/ds/symlink/lm317.pdf",
        snippet="Adjustable 3-terminal positive voltage regulator.",
        provider="google_cse",
        rank=1,
    )

    assert r.domain == "ti.com"
    assert r.title == "TI LM317 Regulator"
    assert r.provider == "google_cse"


def test_search_response_collection_behavior(sample_query, sample_results):
    resp = SearchResponse(
        query=sample_query,
        results=tuple(sample_results),
        provider_used="mock",
        duration_ms=45.2,
    )

    assert len(resp) == 3
    assert bool(resp) is True
    assert resp.first().title == sample_results[0].title
    assert resp[1].url == sample_results[1].url
    assert len(resp.urls) == 3
    assert resp.urls[0] == sample_results[0].url

    # Check iteration
    titles = [item.title for item in resp]
    assert len(titles) == 3
    assert titles[0] == "Murata BLM18PG121SN1D Datasheet"


def test_empty_search_response(sample_query):
    resp = SearchResponse(
        query=sample_query,
        results=(),
        provider_used=None,
        duration_ms=10.0,
        error="All providers failed",
    )

    assert len(resp) == 0
    assert bool(resp) is False
    assert resp.first() is None
    assert resp.urls == ()
    assert resp.error == "All providers failed"

