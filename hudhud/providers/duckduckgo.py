"""
DuckDuckGo search provider adapter (free web scraping via ddgs).
Requires no API keys.
"""

from __future__ import annotations

from typing import Sequence

from ddgs import DDGS

from hudhud.exceptions import ProviderError
from hudhud.primitives import SearchQuery, SearchResult
from hudhud.providers.base import BaseProvider


class DuckDuckGoProvider(BaseProvider):
    """DuckDuckGo provider using the ddgs library."""

    @property
    def name(self) -> str:
        return "duckduckgo"

    def _execute_search(self, query: SearchQuery) -> Sequence[SearchResult]:
        try:
            # ddgs DDGS().text() returns an iterable of result dicts
            raw_items = DDGS().text(query.text, max_results=query.limit)
            items = list(raw_items)
        except Exception as e:
            raise ProviderError(self.name, f"DuckDuckGo search failed: {e}", original_exception=e) from e

        results: list[SearchResult] = []
        for item in items:
            link = item.get("href")
            if not link:
                continue
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=link,
                    snippet=item.get("body", ""),
                    provider=self.name,
                    raw=item,
                )
            )

        return results
