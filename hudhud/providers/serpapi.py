"""
SerpAPI (Google Search API) provider adapter.
Docs: https://serpapi.com/search-api
"""

from __future__ import annotations

from typing import Sequence

import requests

from hudhud.exceptions import AuthenticationError, ProviderError, RateLimitError
from hudhud.primitives import SearchQuery, SearchResult
from hudhud.providers.base import BaseProvider


class SerpAPIProvider(BaseProvider):
    """SerpAPI Google Search provider."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("SerpAPIProvider requires a non-empty api_key.")
        self.api_key = api_key.strip()

    @property
    def name(self) -> str:
        return "serpapi"

    def _execute_search(self, query: SearchQuery) -> Sequence[SearchResult]:
        url = "https://serpapi.com/search"
        params = {
            "q": query.text,
            "api_key": self.api_key,
            "engine": "google",
            "num": min(max(query.limit, 1), 10),
            "hl": "en",
            "gl": "us",
        }

        resp = requests.get(url, params=params, timeout=query.timeout_seconds)

        if resp.status_code == 429:
            raise RateLimitError(self.name, "Rate limit exceeded (HTTP 429)", status_code=429)
        if resp.status_code in (401, 403):
            raise AuthenticationError(
                self.name, f"Authentication failed (HTTP {resp.status_code})", status_code=resp.status_code
            )
        if not resp.ok:
            raise ProviderError(self.name, f"HTTP request failed: status {resp.status_code}", status_code=resp.status_code)

        try:
            data = resp.json()
            items = data.get("organic_results", [])
        except Exception as e:
            raise ProviderError(self.name, f"Failed to parse JSON response: {e}") from e

        results: list[SearchResult] = []
        for item in items:
            link = item.get("link")
            if not link:
                continue
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=link,
                    snippet=item.get("snippet", ""),
                    provider=self.name,
                    raw=item,
                )
            )

        return results
