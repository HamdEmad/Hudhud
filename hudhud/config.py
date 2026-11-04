"""
Configuration and environment resolution for search provider credentials.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _load_dotenv_if_available() -> None:
    """Attempt to load a .env file if python-dotenv is installed."""
    try:
        from dotenv import find_dotenv, load_dotenv

        env_file = find_dotenv(usecwd=True)
        if env_file:
            load_dotenv(env_file)
    except ImportError:
        pass


@dataclass(frozen=True)
class ProviderConfig:
    """
    Credentials for all supported external search providers.
    """

    google_cse_api_key: Optional[str] = None
    google_cse_cx: Optional[str] = None
    serp_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    jina_api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> ProviderConfig:
        """Construct ProviderConfig by reading system environment variables and .env file."""
        _load_dotenv_if_available()
        return cls(
            google_cse_api_key=os.environ.get("GOOGLE_CSE_API_KEY"),
            google_cse_cx=os.environ.get("GOOGLE_CSE_CX"),
            serp_api_key=os.environ.get("SERP_API_KEY"),
            firecrawl_api_key=os.environ.get("FIRECRAWL_API_KEY"),
            tavily_api_key=os.environ.get("TAVILY_API_KEY"),
            jina_api_key=os.environ.get("JINA_API_KEY"),
        )

