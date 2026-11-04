"""
DuckDuckGo search provider adapter (free web search via ddgs).
Supports multi-engine backends: duckduckgo, brave, yandex, startpage, yahoo, wikipedia, mojeek, grokipedia, auto.
Requires no API keys.
"""

from __future__ import annotations

from typing import Sequence

from ddgs import DDGS

from hudhud.exceptions import ProviderError
from hudhud.primitives import SearchQuery, SearchResult
from hudhud.providers.base import BaseProvider


class DuckDuckGoProvider(BaseProvider):
    """
    DuckDuckGo / Open Search provider using the ddgs library.

    Supports custom engine backends via the `backend` argument:
        - 'auto' (default: pools and shuffles available free engines)
        - 'duckduckgo'
        - 'brave'
        - 'yandex'
        - 'wikipedia'
        - 'startpage'
        - 'yahoo'
        - 'mojeek'
        - 'grokipedia'
    """

    def __init__(self, backend: str = "auto") -> None:
        self.backend = (backend or "auto").strip().lower()

    @property
    def name(self) -> str:
        if self.backend in ("auto", "duckduckgo"):
            return "duckduckgo"
        return f"duckduckgo:{self.backend}"

    def _execute_search(self, query: SearchQuery) -> Sequence[SearchResult]:
        try:
            # ddgs DDGS().text() returns an iterable of result dicts
            raw_items = DDGS().text(query.text, backend=self.backend, max_results=query.limit)
            items = list(raw_items)
        except Exception as e:
            raise ProviderError(self.name, f"Search failed via [{self.backend}]: {e}", original_exception=e) from e

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
