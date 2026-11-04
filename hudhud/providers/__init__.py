"""
Provider registry and factory functions.
"""

from __future__ import annotations

from typing import Optional

from hudhud.config import ProviderConfig
from hudhud.interfaces import SearchProvider
from hudhud.providers.base import BaseProvider
from hudhud.providers.duckduckgo import DuckDuckGoProvider
from hudhud.providers.firecrawl import FirecrawlProvider
from hudhud.providers.google_cse import GoogleCSEProvider
from hudhud.providers.jina import JinaProvider
from hudhud.providers.serpapi import SerpAPIProvider
from hudhud.providers.tavily import TavilyProvider

__all__ = [
    "BaseProvider",
    "GoogleCSEProvider",
    "SerpAPIProvider",
    "TavilyProvider",
    "FirecrawlProvider",
    "DuckDuckGoProvider",
    "JinaProvider",
    "create_provider",
]


def create_provider(
    name: str,
    config: Optional[ProviderConfig] = None,
    **kwargs: str,
) -> Optional[SearchProvider]:
    """
    Factory to instantiate a SearchProvider by name.

    Returns None if required API credentials are absent.
    """
    key = name.strip().lower()
    cfg = config or ProviderConfig.from_env()

    if key in ("google_cse", "google", "cse"):
        api_key = kwargs.get("api_key") or cfg.google_cse_api_key
        cx = kwargs.get("cx") or cfg.google_cse_cx
        if api_key and cx:
            return GoogleCSEProvider(api_key=api_key, cx=cx)
        return None

    if key in ("serpapi", "serp"):
        api_key = kwargs.get("api_key") or cfg.serp_api_key
        if api_key:
            return SerpAPIProvider(api_key=api_key)
        return None

    if key in ("tavily",):
        api_key = kwargs.get("api_key") or cfg.tavily_api_key
        if api_key:
            return TavilyProvider(api_key=api_key)
        return None

    if key in ("firecrawl",):
        api_key = kwargs.get("api_key") or cfg.firecrawl_api_key
        if api_key:
            return FirecrawlProvider(api_key=api_key)
        return None

    if key in ("duckduckgo", "ddg"):
        return DuckDuckGoProvider()

    if key in ("jina",):
        api_key = kwargs.get("api_key") or cfg.jina_api_key
        if api_key:
            return JinaProvider(api_key=api_key)
        return None

    raise ValueError(f"Unknown search provider: '{name}'")
