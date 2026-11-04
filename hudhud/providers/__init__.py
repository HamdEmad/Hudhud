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

    def _get_credential(param: str, env_val: Optional[str]) -> Optional[str]:
        if param in kwargs:
            val = kwargs[param]
            return val.strip() if val and val.strip() else None
        return env_val

    if key in ("google_cse", "google", "cse"):
        api_key = _get_credential("api_key", cfg.google_cse_api_key)
        cx = _get_credential("cx", cfg.google_cse_cx)
        if api_key and cx:
            return GoogleCSEProvider(api_key=api_key, cx=cx)
        return None

    if key in ("serpapi", "serp"):
        api_key = _get_credential("api_key", cfg.serp_api_key)
        if api_key:
            return SerpAPIProvider(api_key=api_key)
        return None

    if key in ("tavily",):
        api_key = _get_credential("api_key", cfg.tavily_api_key)
        if api_key:
            return TavilyProvider(api_key=api_key)
        return None

    if key in ("firecrawl",):
        api_key = _get_credential("api_key", cfg.firecrawl_api_key)
        if api_key:
            return FirecrawlProvider(api_key=api_key)
        return None

    if key in ("duckduckgo", "ddg"):
        backend = kwargs.get("backend", "auto")
        return DuckDuckGoProvider(backend=backend)

    # Free open search engine backends powered by ddgs
    if key in ("brave", "yandex", "startpage", "wikipedia", "mojeek", "yahoo", "grokipedia"):
        return DuckDuckGoProvider(backend=key)

    if key in ("jina",):
        api_key = _get_credential("api_key", cfg.jina_api_key)
        if api_key:
            return JinaProvider(api_key=api_key)
        return None

    raise ValueError(f"Unknown search provider: '{name}'")

