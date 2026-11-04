"""
Exceptions: hierarchy of errors for Hudhud.

Designed so callers can catch high-level exceptions or inspect granular provider failures.
"""

from __future__ import annotations

from typing import Optional


class HudhudError(Exception):
    """Base exception for all errors raised by the Hudhud library."""


class InvalidQueryError(HudhudError):
    """Raised when an invalid search query or parameter is provided."""


class ProviderError(HudhudError):
    """Raised when an external search provider fails."""

    def __init__(
        self,
        provider: str,
        message: str,
        status_code: Optional[int] = None,
        original_exception: Optional[Exception] = None,
    ) -> None:
        super().__init__(f"[{provider}] {message}")
        self.provider = provider
        self.message = message
        self.status_code = status_code
        self.original_exception = original_exception


class RateLimitError(ProviderError):
    """Raised when a provider rejects a request due to rate limiting (HTTP 429)."""


class AuthenticationError(ProviderError):
    """Raised when a provider rejects credentials (HTTP 401 / 403)."""


class AllProvidersExhaustedError(HudhudError):
    """Raised when all configured providers have been attempted and failed."""

    def __init__(self, query_text: str, attempted_providers: list[str]) -> None:
        super().__init__(
            f"All providers exhausted for query '{query_text}'. Attempted: {attempted_providers}"
        )
        self.query_text = query_text
        self.attempted_providers = attempted_providers

