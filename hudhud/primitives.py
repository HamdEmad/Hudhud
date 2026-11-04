"""
Primitives: immutable, zero-dependency core data structures for Hudhud.

Designed according to Eskil Steenberg's Primitive-First design principle:
- Simple, predictable, and immutable (frozen dataclasses).
- Self-contained: does not depend on any third-party library or provider.
- Everything in the system flows around these primitives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional, Sequence, Tuple
from urllib.parse import urlparse


def _clean_domain(domain: str) -> str:
    """Normalize a domain string by stripping protocol, trailing slash, and www."""
    d = domain.strip().lower()
    if d.startswith("http://") or d.startswith("https://"):
        parsed = urlparse(d)
        d = parsed.netloc or parsed.path
    if d.startswith("www."):
        d = d[4:]
    return d.rstrip("/")


@dataclass(frozen=True)
class SearchQuery:
    """
    Immutable specification of a web search request.
    """

    text: str
    limit: int = 10
    allowed_domains: Tuple[str, ...] = ()
    excluded_domains: Tuple[str, ...] = ()
    timeout_seconds: float = 15.0
    inter_request_delay_seconds: float = 0.0

    def __post_init__(self) -> None:
        clean_text = self.text.strip()
        if not clean_text:
            raise ValueError("SearchQuery text cannot be empty or blank.")
        if self.limit < 1:
            raise ValueError(f"SearchQuery limit must be at least 1, got {self.limit}.")
        if self.timeout_seconds <= 0:
            raise ValueError(f"SearchQuery timeout_seconds must be positive, got {self.timeout_seconds}.")

        # Normalize domains
        clean_allowed = tuple(_clean_domain(d) for d in self.allowed_domains if d.strip())
        clean_excluded = tuple(_clean_domain(d) for d in self.excluded_domains if d.strip())

        object.__setattr__(self, "text", clean_text)
        object.__setattr__(self, "allowed_domains", clean_allowed)
        object.__setattr__(self, "excluded_domains", clean_excluded)

    def matches_domain_rules(self, url: str) -> bool:
        """
        Check if a given URL complies with allowed and excluded domain rules.
        """
        if not url:
            return False

        try:
            parsed = urlparse(url)
            netloc = (parsed.netloc or parsed.path).lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
        except Exception:
            return False

        # Excluded domains check
        for excluded in self.excluded_domains:
            if netloc == excluded or netloc.endswith("." + excluded):
                return False

        # Allowed domains check (if none specified, all non-excluded domains pass)
        if not self.allowed_domains:
            return True

        for allowed in self.allowed_domains:
            if netloc == allowed or netloc.endswith("." + allowed):
                return True

        return False


@dataclass(frozen=True)
class SearchResult:
    """
    Immutable representation of an individual search result item.
    """

    title: str
    url: str
    snippet: str
    provider: str
    rank: int = 0
    score: Optional[float] = None
    raw: dict = field(default_factory=dict, hash=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", self.title.strip() if self.title else "")
        object.__setattr__(self, "url", self.url.strip() if self.url else "")
        object.__setattr__(self, "snippet", self.snippet.strip() if self.snippet else "")
        object.__setattr__(self, "provider", self.provider.strip() if self.provider else "")

    @property
    def domain(self) -> str:
        """Extract the registered hostname / domain from the result URL."""
        if not self.url:
            return ""
        try:
            parsed = urlparse(self.url)
            netloc = (parsed.netloc or parsed.path).lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc
        except Exception:
            return ""


@dataclass(frozen=True)
class SearchResponse:
    """
    Immutable container returned by a search execution.
    Acts as a collection of SearchResult items with rich metadata.
    """

    query: SearchQuery
    results: Tuple[SearchResult, ...] = ()
    provider_used: Optional[str] = None
    duration_ms: float = 0.0
    is_cached: bool = False
    error: Optional[str] = None

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self) -> Iterator[SearchResult]:
        return iter(self.results)

    def __getitem__(self, index: int) -> SearchResult:
        return self.results[index]

    def __bool__(self) -> bool:
        return len(self.results) > 0

    def first(self) -> Optional[SearchResult]:
        """Return the first result item or None if empty."""
        return self.results[0] if self.results else None

    @property
    def urls(self) -> Tuple[str, ...]:
        """Return a tuple of all result URLs in rank order."""
        return tuple(r.url for r in self.results)

