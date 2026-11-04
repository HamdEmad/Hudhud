"""
Shared test fixtures and mock providers for Hudhud test suite.
"""

from __future__ import annotations

from typing import List, Optional, Sequence
import pytest

from hudhud.interfaces import SearchProvider
from hudhud.primitives import SearchQuery, SearchResult
from hudhud.exceptions import ProviderError, RateLimitError


class MockProvider(SearchProvider):
    """Configurable mock provider for testing fallback chains and caching."""

    def __init__(
        self,
        name: str = "mock",
        results: Optional[List[SearchResult]] = None,
        should_fail: bool = False,
        error_type: str = "generic",
    ) -> None:
        self._name = name
        self.results = results if results is not None else []
        self.should_fail = should_fail
        self.error_type = error_type
        self.call_count = 0
        self.last_query: Optional[SearchQuery] = None

    @property
    def name(self) -> str:
        return self._name

    def search(self, query: SearchQuery) -> Sequence[SearchResult]:
        self.call_count += 1
        self.last_query = query

        if self.should_fail:
            if self.error_type == "rate_limit":
                raise RateLimitError(self.name, "Rate limit exceeded (HTTP 429)", 429)
            raise ProviderError(self.name, "Provider internal error")

        # Domain filtering
        filtered = [
            r for r in self.results
            if not query.allowed_domains or any(query.matches_domain_rules(r.url) for _ in [1])
        ]
        return filtered[: query.limit]


@pytest.fixture
def sample_query() -> SearchQuery:
    return SearchQuery(
        text="Murata BLM18PG121SN1D",
        limit=5,
        allowed_domains=("murata.com", "mouser.com"),
    )


@pytest.fixture
def sample_results() -> List[SearchResult]:
    return [
        SearchResult(
            title="Murata BLM18PG121SN1D Datasheet",
            url="https://www.murata.com/products/productdetail?partno=BLM18PG121SN1D",
            snippet="Chip ferrite bead for power lines, 120 Ohm at 100MHz.",
            provider="mock",
            rank=1,
        ),
        SearchResult(
            title="Mouser BLM18PG121SN1D Inventory",
            url="https://www.mouser.com/ProductDetail/Murata/BLM18PG121SN1D",
            snippet="In stock, 10,000 units available for immediate shipping.",
            provider="mock",
            rank=2,
        ),
        SearchResult(
            title="DigiKey Component Index",
            url="https://www.digikey.com/en/products/detail/murata/BLM18PG121SN1D",
            snippet="DigiKey component details and stock.",
            provider="mock",
            rank=3,
        ),
    ]
