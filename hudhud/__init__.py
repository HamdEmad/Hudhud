"""
Hudhud (هُدْهُد) - A resilient, chained multi-backend web search library for Python.
"""

from __future__ import annotations

from hudhud.cache.memory import MemoryCache
from hudhud.cache.sqlite import SqliteCache
from hudhud.chain import Hudhud
from hudhud.config import ProviderConfig
from hudhud.exceptions import (
    AllProvidersExhaustedError,
    AuthenticationError,
    HudhudError,
    InvalidQueryError,
    ProviderError,
    RateLimitError,
)
from hudhud.interfaces import SearchCache, SearchProvider
from hudhud.primitives import SearchQuery, SearchResponse, SearchResult
from hudhud.providers import (
    BaseProvider,
    DuckDuckGoProvider,
    FirecrawlProvider,
    GoogleCSEProvider,
    JinaProvider,
    SerpAPIProvider,
    TavilyProvider,
    create_provider,
)

__version__ = "0.1.0"

__all__ = [
    # Core Orchestration
    "Hudhud",
    "__version__",
    # Primitives
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    # Interfaces
    "SearchProvider",
    "SearchCache",
    # Configuration
    "ProviderConfig",
    # Caches
    "MemoryCache",
    "SqliteCache",
    # Providers
    "BaseProvider",
    "GoogleCSEProvider",
    "SerpAPIProvider",
    "TavilyProvider",
    "FirecrawlProvider",
    "DuckDuckGoProvider",
    "JinaProvider",
    "create_provider",
    # Exceptions
    "HudhudError",
    "InvalidQueryError",
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "AllProvidersExhaustedError",
]
