"""
Base abstract class for all Hudhud search providers.

Handles:
- Common exception wrapping (translates requests/network exceptions to ProviderError).
- Domain whitelisting & blacklisting filtering via SearchQuery primitives.
- Result ranking and limit enforcement.
"""

from __future__ import annotations

import abc
import logging
from typing import Sequence

import requests

from hudhud.exceptions import AuthenticationError, ProviderError, RateLimitError
from hudhud.interfaces import SearchProvider
from hudhud.primitives import SearchQuery, SearchResult

logger = logging.getLogger(__name__)


class BaseProvider(abc.ABC, SearchProvider):
    """
    Abstract base search provider.

    Subclasses implement `_execute_search(query)`.
    `BaseProvider.search(query)` wraps errors, enforces domain filters,
    and formats rank numbers.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        ...

    @abc.abstractmethod
    def _execute_search(self, query: SearchQuery) -> Sequence[SearchResult]:
        """Subclasses implement raw API interaction here."""
        ...

    def search(self, query: SearchQuery) -> list[SearchResult]:
        """
        Execute search with error handling and domain filtering.
        """
        try:
            raw_results = self._execute_search(query)
        except requests.exceptions.RequestException as e:
            resp = getattr(e, "response", None)
            status_code = resp.status_code if resp is not None else None

            if status_code == 429:
                raise RateLimitError(
                    provider=self.name,
                    message="Rate limit exceeded (HTTP 429)",
                    status_code=429,
                    original_exception=e,
                ) from e
            elif status_code in (401, 403):
                raise AuthenticationError(
                    provider=self.name,
                    message=f"Authentication failed (HTTP {status_code})",
                    status_code=status_code,
                    original_exception=e,
                ) from e
            else:
                raise ProviderError(
                    provider=self.name,
                    message=f"Network request failed: {e}",
                    status_code=status_code,
                    original_exception=e,
                ) from e
        except ProviderError:
            # Re-raise ProviderErrors directly
            raise
        except Exception as e:
            raise ProviderError(
                provider=self.name,
                message=f"Unexpected error during search: {e}",
                original_exception=e,
            ) from e

        # Filter by allowed/excluded domains
        filtered_results: list[SearchResult] = []
        for item in raw_results:
            if not item.url:
                continue
            if query.matches_domain_rules(item.url):
                filtered_results.append(item)

        # Truncate to limit and set 1-based ranks
        final_results: list[SearchResult] = []
        for rank_idx, item in enumerate(filtered_results[: query.limit], start=1):
            final_results.append(
                SearchResult(
                    title=item.title,
                    url=item.url,
                    snippet=item.snippet,
                    provider=self.name,
                    rank=rank_idx,
                    score=item.score,
                    raw=item.raw,
                )
            )

        return final_results
