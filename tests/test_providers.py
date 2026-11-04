"""
Unit tests for individual search providers and BaseProvider adapter mechanics.
"""

from unittest.mock import MagicMock, patch
import pytest

from hudhud.exceptions import AuthenticationError, ProviderError, RateLimitError
from hudhud.primitives import SearchQuery
from hudhud.providers.google_cse import GoogleCSEProvider
from hudhud.providers.serpapi import SerpAPIProvider
from hudhud.providers.tavily import TavilyProvider
from hudhud.providers.firecrawl import FirecrawlProvider
from hudhud.providers.duckduckgo import DuckDuckGoProvider
from hudhud.providers.jina import JinaProvider
from hudhud.providers import create_provider


def test_provider_factory():
    # DuckDuckGo requires no keys
    ddg = create_provider("duckduckgo")
    assert ddg is not None
    assert ddg.name == "duckduckgo"

    # Missing keys return None
    assert create_provider("google_cse", api_key="", cx="") is None
    assert create_provider("serpapi", api_key="") is None

    # Providing explicit keys works
    cse = create_provider("google_cse", api_key="k", cx="c")
    assert cse is not None
    assert cse.name == "google_cse"


@patch("hudhud.providers.google_cse.requests.get")
def test_google_cse_provider_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "items": [
            {"title": "ST Part", "link": "https://www.st.com/stm32", "snippet": "Microcontroller"}
        ]
    }
    mock_get.return_value = mock_resp

    provider = GoogleCSEProvider(api_key="fake-key", cx="fake-cx")
    query = SearchQuery(text="stm32", limit=5)
    results = provider.search(query)

    assert len(results) == 1
    assert results[0].title == "ST Part"
    assert results[0].url == "https://www.st.com/stm32"
    assert results[0].provider == "google_cse"
    assert results[0].rank == 1


@patch("hudhud.providers.google_cse.requests.get")
def test_google_cse_rate_limit(mock_get):
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 429
    mock_get.return_value = mock_resp

    provider = GoogleCSEProvider(api_key="fake-key", cx="fake-cx")
    query = SearchQuery(text="stm32")

    with pytest.raises(RateLimitError):
        provider.search(query)


@patch("hudhud.providers.serpapi.requests.get")
def test_serpapi_provider_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "organic_results": [
            {"title": "TI Part", "link": "https://www.ti.com/opamp", "snippet": "Op-Amp"}
        ]
    }
    mock_get.return_value = mock_resp

    provider = SerpAPIProvider(api_key="fake-key")
    query = SearchQuery(text="opamp", limit=5)
    results = provider.search(query)

    assert len(results) == 1
    assert results[0].title == "TI Part"
    assert results[0].provider == "serpapi"


@patch("hudhud.providers.tavily.requests.post")
def test_tavily_provider_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"title": "Tavily Result", "url": "https://example.com", "content": "Sample content"}
        ]
    }
    mock_post.return_value = mock_resp

    provider = TavilyProvider(api_key="fake-key")
    query = SearchQuery(text="ai search", limit=5)
    results = provider.search(query)

    assert len(results) == 1
    assert results[0].title == "Tavily Result"
    assert results[0].provider == "tavily"


@patch("hudhud.providers.firecrawl.requests.post")
def test_firecrawl_provider_auth_error(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 401
    mock_post.return_value = mock_resp

    provider = FirecrawlProvider(api_key="invalid-key")
    query = SearchQuery(text="crawl search")

    with pytest.raises(AuthenticationError):
        provider.search(query)


@patch("hudhud.providers.duckduckgo.DDGS")
def test_duckduckgo_provider_success(mock_ddgs_cls):
    mock_ddgs_instance = MagicMock()
    mock_ddgs_instance.text.return_value = [
        {"title": "DDG Title", "href": "https://duckduckgo.com/sample", "body": "DDG Snippet"}
    ]
    mock_ddgs_cls.return_value = mock_ddgs_instance

    provider = DuckDuckGoProvider()
    query = SearchQuery(text="open search", limit=5)
    results = provider.search(query)

    assert len(results) == 1
    assert results[0].title == "DDG Title"
    assert results[0].url == "https://duckduckgo.com/sample"
    assert results[0].provider == "duckduckgo"


@patch("hudhud.providers.jina.requests.get")
def test_jina_provider_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"title": "Jina Result", "url": "https://jina.ai/doc", "description": "Doc description"}
        ]
    }
    mock_get.return_value = mock_resp

    provider = JinaProvider(api_key="fake-key")
    query = SearchQuery(text="jina query", limit=5)
    results = provider.search(query)

    assert len(results) == 1
    assert results[0].title == "Jina Result"
    assert results[0].provider == "jina"
