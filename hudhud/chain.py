"""
Chain: Fluent method-chaining pipeline orchestrator for Hudhud.

Implements the builder pattern:
    Hudhud()
    .scout("search text")
    .via("google_cse")
    .fallback_to("tavily")
    .fallback_to("duckduckgo")
    .allow_domains(["st.com", "ti.com"])
    .exclude_domains(["pinterest.com"])
    .limit(5)
    .with_cache(ttl_seconds=86400)
    .fly()
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Iterable, List, Optional, Sequence, Union

from hudhud.cache.memory import MemoryCache
from hudhud.cache.sqlite import SqliteCache
from hudhud.config import ProviderConfig
from hudhud.exceptions import AllProvidersExhaustedError, HudhudError, InvalidQueryError, ProviderError
from hudhud.interfaces import SearchCache, SearchProvider
from hudhud.primitives import SearchQuery, SearchResponse, SearchResult
from hudhud.providers import create_provider

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER_CHAIN = (
    "google_cse",
    "serpapi",
    "firecrawl",
    "tavily",
    "duckduckgo",
    "jina",
)


class Hudhud:
    """
    Fluent builder for constructing and executing resilient web search pipelines.
    """

    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        self._config = config or ProviderConfig.from_env()
        self._query_text: Optional[str] = None
        self._limit: int = 10
        self._timeout_seconds: float = 15.0
        self._inter_request_delay_seconds: float = 0.0
        self._allowed_domains: List[str] = []
        self._excluded_domains: List[str] = []
        self._configured_providers: List[SearchProvider] = []
        self._cache: Optional[SearchCache] = None
        self._cache_ttl_seconds: int = 86400
        self._strict_mode: bool = False

    def scout(self, query: str) -> Hudhud:
        """Set the search query string."""
        if not query or not query.strip():
            raise InvalidQueryError("Search query cannot be empty or whitespace.")
        self._query_text = query.strip()
        return self

    def via(
        self,
        provider: Union[str, SearchProvider],
        **kwargs: Any,
    ) -> Hudhud:
        """
        Set or prepend the primary search provider.
        """
        resolved = self._resolve_provider(provider, **kwargs)
        if resolved is not None:
            # Insert at the beginning or replace empty
            self._configured_providers = [resolved]
        return self

    def fallback_to(
        self,
        provider: Union[str, SearchProvider],
        **kwargs: Any,
    ) -> Hudhud:
        """
        Append a fallback provider to the execution chain.
        """
        resolved = self._resolve_provider(provider, **kwargs)
        if resolved is not None:
            # Check not already present
            if not any(p.name == resolved.name for p in self._configured_providers):
                self._configured_providers.append(resolved)
        return self

    def allow_domains(self, domains: Iterable[str]) -> Hudhud:
        """Specify domains that results MUST come from."""
        for d in domains:
            if d and d.strip():
                self._allowed_domains.append(d.strip())
        return self

    def exclude_domains(self, domains: Iterable[str]) -> Hudhud:
        """Specify domains that results MUST NOT come from."""
        for d in domains:
            if d and d.strip():
                self._excluded_domains.append(d.strip())
        return self

    def limit(self, count: int) -> Hudhud:
        """Set the maximum number of results to retrieve (must be >= 1)."""
        if count < 1:
            raise InvalidQueryError(f"limit must be >= 1, got {count}")
        self._limit = count
        return self

    def timeout(self, seconds: float) -> Hudhud:
        """Set per-request network timeout in seconds."""
        if seconds <= 0:
            raise InvalidQueryError(f"timeout must be > 0, got {seconds}")
        self._timeout_seconds = seconds
        return self

    def delay(self, seconds: float) -> Hudhud:
        """Set delay between provider fallback requests in seconds."""
        self._inter_request_delay_seconds = max(0.0, seconds)
        return self

    def with_cache(
        self,
        cache: Optional[Union[SearchCache, str]] = None,
        ttl_seconds: int = 86400,
    ) -> Hudhud:
        """
        Enable result caching.

        Args:
            cache: None or 'sqlite' for SqliteCache, 'memory' for MemoryCache,
                   or a custom instance implementing SearchCache.
            ttl_seconds: Time to live in seconds (default 24 hours).
        """
        self._cache_ttl_seconds = max(1, ttl_seconds)
        if cache is None or (isinstance(cache, str) and cache.lower() == "sqlite"):
            self._cache = SqliteCache()
        elif isinstance(cache, str) and cache.lower() == "memory":
            self._cache = MemoryCache()
        elif isinstance(cache, SearchCache):
            self._cache = cache
        else:
            raise ValueError(f"Unsupported cache backend: {cache}")
        return self

    def without_cache(self) -> Hudhud:
        """Disable caching."""
        self._cache = None
        return self

    def strict(self, enabled: bool = True) -> Hudhud:
        """
        If True, raise AllProvidersExhaustedError when all providers fail.
        If False (default), return an empty SearchResponse.
        """
        self._strict_mode = enabled
        return self

    def _resolve_provider(
        self,
        provider: Union[str, SearchProvider],
        **kwargs: Any,
    ) -> Optional[SearchProvider]:
        """Convert a provider string name or instance into a SearchProvider."""
        if isinstance(provider, SearchProvider):
            return provider
        if isinstance(provider, str):
            return create_provider(provider, config=self._config, **kwargs)
        raise TypeError(f"Expected str or SearchProvider, got {type(provider)}")

    def _get_active_chain(self) -> List[SearchProvider]:
        """
        Return the list of providers to attempt.
        If user explicitly called .via() or .fallback_to(), use those.
        Otherwise, build the default fallback chain based on available credentials.
        """
        if self._configured_providers:
            return list(self._configured_providers)

        default_chain: List[SearchProvider] = []
        for name in DEFAULT_PROVIDER_CHAIN:
            p = create_provider(name, config=self._config)
            if p is not None:
                default_chain.append(p)
        return default_chain

    def fly(self) -> SearchResponse:
        """
        Execute the search pipeline synchronously and return the SearchResponse.
        """
        if not self._query_text:
            raise InvalidQueryError("No search query specified. Call .scout('...') first.")

        query = SearchQuery(
            text=self._query_text,
            limit=self._limit,
            allowed_domains=tuple(self._allowed_domains),
            excluded_domains=tuple(self._excluded_domains),
            timeout_seconds=self._timeout_seconds,
            inter_request_delay_seconds=self._inter_request_delay_seconds,
        )

        providers = self._get_active_chain()
        if not providers:
            msg = "No search providers are available or configured with valid credentials."
            logger.error("Hudhud: %s", msg)
            if self._strict_mode:
                raise AllProvidersExhaustedError(query.text, [])
            return SearchResponse(query=query, results=(), error=msg)

        start_time = time.perf_counter()
        attempted_provider_names: List[str] = []

        # 1. Check cache first across all providers in chain
        if self._cache is not None:
            for p in providers:
                cached = self._cache.get(query, p.name)
                if cached is not None and len(cached) > 0:
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    logger.info("Hudhud: cache hit for query '%s' from '%s'", query.text[:40], p.name)
                    return SearchResponse(
                        query=query,
                        results=tuple(cached),
                        provider_used=p.name,
                        duration_ms=duration_ms,
                        is_cached=True,
                    )

        # 2. Sequential fallback execution
        for i, provider in enumerate(providers):
            attempted_provider_names.append(provider.name)
            logger.info("Hudhud [%d/%d]: attempting provider '%s'", i + 1, len(providers), provider.name)

            try:
                results = provider.search(query)
                if results:
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    logger.info(
                        "Hudhud: '%s' returned %d results via '%s' in %.1fms",
                        query.text[:40],
                        len(results),
                        provider.name,
                        duration_ms,
                    )

                    # Store in cache if enabled
                    if self._cache is not None:
                        try:
                            self._cache.set(query, provider.name, results, self._cache_ttl_seconds)
                        except Exception as cache_err:
                            logger.warning("Hudhud: failed to write to cache: %s", cache_err)

                    return SearchResponse(
                        query=query,
                        results=tuple(results),
                        provider_used=provider.name,
                        duration_ms=duration_ms,
                        is_cached=False,
                    )

                logger.warning(
                    "Hudhud: provider '%s' returned 0 results for '%s'. Cascading...",
                    provider.name,
                    query.text[:40],
                )

            except ProviderError as e:
                logger.warning("Hudhud: provider '%s' failed: %s. Cascading...", provider.name, e)
            except Exception as e:
                logger.warning("Hudhud: unexpected error from provider '%s': %s. Cascading...", provider.name, e)

            # Delay before next provider
            if i < len(providers) - 1 and self._inter_request_delay_seconds > 0:
                time.sleep(self._inter_request_delay_seconds)

        # All providers exhausted
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(
            "Hudhud: all %d providers exhausted for query '%s'",
            len(providers),
            query.text[:40],
        )

        if self._strict_mode:
            raise AllProvidersExhaustedError(query.text, attempted_provider_names)

        return SearchResponse(
            query=query,
            results=(),
            provider_used=None,
            duration_ms=duration_ms,
            is_cached=False,
            error=f"All providers exhausted: {attempted_provider_names}",
        )

    async def fly_async(self) -> SearchResponse:
        """
        Execute the search pipeline asynchronously via thread pool.
        """
        return await asyncio.to_thread(self.fly)
