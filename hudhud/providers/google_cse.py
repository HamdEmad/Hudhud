"""
Google Custom Search JSON API provider adapter.
Docs: https://developers.google.com/custom-search/v1/overview
"""

from __future__ import annotations

from typing import Sequence

import requests

from hudhud.exceptions import AuthenticationError, ProviderError, RateLimitError
from hudhud.primitives import SearchQuery, SearchResult
from hudhud.providers.base import BaseProvider


class GoogleCSEProvider(BaseProvider):
    """Google Custom Search Engine (CSE) provider."""

    def __init__(self, api_key: str, cx: str) -> None:
        if not api_key or not cx:
            raise ValueError("GoogleCSEProvider requires non-empty api_key and cx.")
        self.api_key = api_key.strip()
        self.cx = cx.strip()

    @property
    def name(self) -> str:
        return "google_cse"

    def _execute_search(self, query: SearchQuery) -> Sequence[SearchResult]:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query.text,
            "num": min(max(query.limit, 1), 10),
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
            items = data.get("items", [])
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

