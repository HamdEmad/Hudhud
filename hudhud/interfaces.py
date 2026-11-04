"""
Interfaces: Black box structural contracts for Hudhud components.

Following Eskil Steenberg's Replaceable Components principle:
- Any module can be rewritten from scratch using only its interface.
- Never expose internal implementation details.
- Uses typing.Protocol for structural subtyping (duck typing with static verification).
"""

from __future__ import annotations

from typing import Optional, Protocol, Sequence, runtime_checkable

from hudhud.primitives import SearchQuery, SearchResult


@runtime_checkable
class SearchProvider(Protocol):
    """
    Contract for any search engine backend provider.
    """

    @property
    def name(self) -> str:
        """Unique identifier of the provider (e.g. 'google_cse', 'duckduckgo')."""
        ...

    def search(self, query: SearchQuery) -> Sequence[SearchResult]:
        """
        Execute a search query and return a sequence of normalized SearchResult items.

        Raises ProviderError or its subclasses on external failure.
        """
        ...


@runtime_checkable
class SearchCache(Protocol):
    """
    Contract for query result caching backends (Memory, SQLite, Redis, etc.).
    """

    def get(self, query: SearchQuery, provider: str) -> Optional[Sequence[SearchResult]]:
        """
        Retrieve cached results for a query and provider, or None if expired/not found.
        """
        ...

    def set(
        self,
        query: SearchQuery,
        provider: str,
        results: Sequence[SearchResult],
        ttl_seconds: int,
    ) -> None:
        """
        Store search results with an expiration time in seconds.
        """
        ...

    def clear(self) -> None:
        """Evict all cached entries."""
        ...

