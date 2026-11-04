"""
In-memory cache implementation with TTL expiration.
"""

from __future__ import annotations

import threading
import time
from typing import Dict, List, Optional, Sequence, Tuple

from hudhud.cache import make_cache_key
from hudhud.interfaces import SearchCache
from hudhud.primitives import SearchQuery, SearchResult


class MemoryCache(SearchCache):
    """
    Fast, thread-safe in-memory cache for search results.
    """

    def __init__(self, max_entries: int = 1000) -> None:
        self._max_entries = max_entries
        self._store: Dict[str, Tuple[float, List[SearchResult]]] = {}
        self._lock = threading.Lock()

    def get(self, query: SearchQuery, provider: str) -> Optional[Sequence[SearchResult]]:
        key = make_cache_key(query, provider)
        now = time.time()

        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None

            expires_at, results = entry
            if now > expires_at:
                # Expired
                del self._store[key]
                return None

            return list(results)

    def set(
        self,
        query: SearchQuery,
        provider: str,
        results: Sequence[SearchResult],
        ttl_seconds: int,
    ) -> None:
        key = make_cache_key(query, provider)
        expires_at = time.time() + max(1, ttl_seconds)

        with self._lock:
            # Simple eviction if max reached
            if len(self._store) >= self._max_entries:
                # Evict oldest expired or random first
                now = time.time()
                expired_keys = [k for k, (exp, _) in self._store.items() if exp < now]
                if expired_keys:
                    for k in expired_keys:
                        del self._store[k]
                elif self._store:
                    first_key = next(iter(self._store))
                    del self._store[first_key]

            self._store[key] = (expires_at, list(results))

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
