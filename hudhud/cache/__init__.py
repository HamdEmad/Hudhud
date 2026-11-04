"""
Cache implementations for Hudhud search queries.
"""

from __future__ import annotations

import hashlib
import json
from typing import Sequence

from hudhud.primitives import SearchQuery, SearchResult


def make_cache_key(query: SearchQuery, provider: str) -> str:
    """Generate a deterministic SHA-256 hash key for a query and provider."""
    raw = json.dumps(
        {
            "p": provider.lower().strip(),
            "t": query.text.lower().strip(),
            "l": query.limit,
            "a": sorted(query.allowed_domains),
            "e": sorted(query.excluded_domains),
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def serialize_results(results: Sequence[SearchResult]) -> str:
    """Serialize a sequence of SearchResult items to JSON."""
    data = [
        {
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet,
            "provider": r.provider,
            "rank": r.rank,
            "score": r.score,
            "raw": r.raw,
        }
        for r in results
    ]
    return json.dumps(data)


def deserialize_results(json_str: str) -> list[SearchResult]:
    """Deserialize JSON back into a list of SearchResult items."""
    raw_list = json.loads(json_str)
    return [
        SearchResult(
            title=item.get("title", ""),
            url=item.get("url", ""),
            snippet=item.get("snippet", ""),
            provider=item.get("provider", ""),
            rank=item.get("rank", 0),
            score=item.get("score"),
            raw=item.get("raw", {}),
        )
        for item in raw_list
    ]
