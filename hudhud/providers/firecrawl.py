"""
Firecrawl Search API provider adapter.
Docs: https://docs.firecrawl.dev
"""

from __future__ import annotations

from typing import Sequence

import requests

from hudhud.exceptions import AuthenticationError, ProviderError, RateLimitError
from hudhud.primitives import SearchQuery, SearchResult
from hudhud.providers.base import BaseProvider


class FirecrawlProvider(BaseProvider):
    """Firecrawl Search API provider."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("FirecrawlProvider requires a non-empty api_key.")
        self.api_key = api_key.strip()

    @property
    def name(self) -> str:
        return "firecrawl"

    def _execute_search(self, query: SearchQuery) -> Sequence[SearchResult]:
        url = "https://api.firecrawl.dev/v1/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query.text,
            "limit": min(max(query.limit, 1), 10),
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=query.timeout_seconds)

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
            items = data.get("data", [])
            if not isinstance(items, list):
                items = []
        except Exception as e:
            raise ProviderError(self.name, f"Failed to parse JSON response: {e}") from e

        results: list[SearchResult] = []
        for item in items:
            link = item.get("url")
            if not link:
                continue
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=link,
                    snippet=item.get("description") or item.get("snippet") or item.get("markdown") or "",
                    provider=self.name,
                    raw=item,
                )
            )

        return results

