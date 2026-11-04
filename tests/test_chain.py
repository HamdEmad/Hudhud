"""
Unit tests for Hudhud fluent builder and fallback orchestration.
"""

import pytest
from hudhud.chain import Hudhud
from hudhud.cache.memory import MemoryCache
from hudhud.exceptions import AllProvidersExhaustedError, InvalidQueryError
from hudhud.primitives import SearchResult
from .conftest import MockProvider


def test_builder_validation():
    with pytest.raises(InvalidQueryError, match="cannot be empty"):
        Hudhud().scout("")

    with pytest.raises(InvalidQueryError, match="limit must be >= 1"):
        Hudhud().scout("valid").limit(0)

    with pytest.raises(InvalidQueryError, match="timeout must be > 0"):
        Hudhud().scout("valid").timeout(-5)


def test_fluent_chain_single_provider_success(sample_results):
    provider = MockProvider("primary", results=sample_results)

    response = (
        Hudhud()
        .scout("Murata ferrite bead")
        .via(provider)
        .limit(2)
        .fly()
    )

    assert response.provider_used == "primary"
    assert len(response) == 2
    assert response.is_cached is False
    assert provider.call_count == 1
    assert response[0].title == sample_results[0].title


def test_fallback_chain_when_primary_fails(sample_results):
    failing_primary = MockProvider("primary", should_fail=True)
    working_secondary = MockProvider("secondary", results=sample_results)

    response = (
        Hudhud()
        .scout("TI OPA2134")
        .via(failing_primary)
        .fallback_to(working_secondary)
        .fly()
    )

    assert failing_primary.call_count == 1
    assert working_secondary.call_count == 1
    assert response.provider_used == "secondary"
    assert len(response) == len(sample_results)


def test_fallback_chain_when_primary_returns_empty(sample_results):
    empty_primary = MockProvider("primary", results=[])
    working_secondary = MockProvider("secondary", results=sample_results)

    response = (
        Hudhud()
        .scout("Microchip ATmega328P")
        .via(empty_primary)
        .fallback_to(working_secondary)
        .fly()
    )

    assert empty_primary.call_count == 1
    assert working_secondary.call_count == 1
    assert response.provider_used == "secondary"
    assert len(response) == len(sample_results)


def test_all_providers_exhausted_default_mode():
    provider1 = MockProvider("p1", should_fail=True)
    provider2 = MockProvider("p2", results=[])

    response = (
        Hudhud()
        .scout("Nonexistent component")
        .via(provider1)
        .fallback_to(provider2)
        .fly()
    )

    assert len(response) == 0
    assert response.provider_used is None
    assert response.error is not None
    assert "All providers exhausted" in response.error


def test_all_providers_exhausted_strict_mode():
    provider1 = MockProvider("p1", should_fail=True)
    provider2 = MockProvider("p2", should_fail=True)

    with pytest.raises(AllProvidersExhaustedError, match="All providers exhausted"):
        (
            Hudhud()
            .scout("Nonexistent component")
            .via(provider1)
            .fallback_to(provider2)
            .strict(True)
            .fly()
        )


def test_caching_integration(sample_results):
    cache = MemoryCache()
    provider = MockProvider("provider_with_cache", results=sample_results)

    # First execution - cache miss
    resp1 = (
        Hudhud()
        .scout("Murata inductor")
        .via(provider)
        .with_cache(cache, ttl_seconds=60)
        .fly()
    )

    assert resp1.is_cached is False
    assert provider.call_count == 1
    assert len(resp1) == len(sample_results)

    # Second execution - cache hit (provider not called again)
    resp2 = (
        Hudhud()
        .scout("Murata inductor")
        .via(provider)
        .with_cache(cache, ttl_seconds=60)
        .fly()
    )

    assert resp2.is_cached is True
    assert provider.call_count == 1  # Still 1!
    assert len(resp2) == len(sample_results)
    assert resp2[0].title == resp1[0].title


def test_domain_filtering_integration():
    raw_results = [
        SearchResult(title="Mouser", url="https://www.mouser.com/part", snippet="ok", provider="p"),
        SearchResult(title="DigiKey", url="https://www.digikey.com/part", snippet="ok", provider="p"),
        SearchResult(title="Pinterest Spam", url="https://pinterest.com/pin", snippet="bad", provider="p"),
    ]
    provider = MockProvider("p", results=raw_results)

    response = (
        Hudhud()
        .scout("part search")
        .via(provider)
        .allow_domains(["mouser.com", "digikey.com"])
        .exclude_domains(["pinterest.com"])
        .fly()
    )

    urls = response.urls
    assert "https://www.mouser.com/part" in urls
    assert "https://www.digikey.com/part" in urls
    assert "https://pinterest.com/pin" not in urls


@pytest.mark.asyncio
async def test_async_flight(sample_results):
    provider = MockProvider("async_provider", results=sample_results)

    response = await (
        Hudhud()
        .scout("Async query")
        .via(provider)
        .limit(2)
        .fly_async()
    )

    assert response.provider_used == "async_provider"
    assert len(response) == 2
    assert provider.call_count == 1
