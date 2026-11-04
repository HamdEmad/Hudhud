# Hudhud (هُدْهُد) 🕊️

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/your-org/hudhud/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/hudhud/actions/workflows/ci.yml)

> *"And he inspected the birds and said, 'Why do I not see the Hudhud...?'"*
> — Named after the legendary scout bird renowned for traversing vast distances, surveying terrain from high altitudes, and returning with precise, verified discoveries.

**Hudhud** is a resilient, chained multi-backend web search library for Python. It provides a fluent, developer-friendly pipeline that lets you scout the web across 6 search engines with automatic failover, transparent SQLite caching, strict domain filtering, and zero vendor lock-in.

---

## ✨ Features

- ⛓️ **Fluent Method-Chaining API**: Expressive builder pattern (`scout().via().fallback_to().fly()`).
- 🔄 **Autonomous Fallback**: Seamlessly cascades across providers if an API fails, hits a rate limit (HTTP 429), or yields 0 results.
- 🔌 **6 Built-in Search Engines**:
  - Google Custom Search Engine (CSE)
  - SerpAPI (Google Search)
  - Tavily AI Search
  - Firecrawl Search
  - DuckDuckGo (Free scraping via `ddgs`, zero keys needed)
  - Jina AI Search (`s.jina.ai`)
- 🛡️ **Eskil Steenberg Architectural Principles**:
  - **Primitive-First**: Immutable data structures (`SearchQuery`, `SearchResult`, `SearchResponse`).
  - **Black Box Interfaces**: Modules communicate only via clean typing `Protocol` interfaces.
  - **Replaceable Components**: Swap or mock providers without touching pipeline code.
  - **No Third-Party Leakage**: External API responses are wrapped immediately into normalized primitives.
- ⚡ **Transparent Caching**: Built-in SQLite & Memory caching with configurable TTL to save API costs and eliminate redundant queries.
- 🎯 **Domain Filtering**: Allow-listing and exclusion lists enforced natively and transparently.

---

## 📦 Installation

```bash
pip install hudhud
```

Or for development:
```bash
git clone https://github.com/your-org/hudhud.git
cd hudhud
pip install -e ".[dev]"
```

---

## 🚀 Quickstart

### 1. Simple Search (Default Fallback)

```python
from hudhud import Hudhud

# Scouts the web using automatically detected API keys,
# falling back to DuckDuckGo if no keys are found.
response = Hudhud().scout("Raspberry Pi 5 pinout").limit(5).fly()

print(f"Provider used: {response.provider_used}")
for result in response:
    print(f"- [{result.title}]({result.url})")
```

### 2. Fluent Fallback Chain

```python
from hudhud import Hudhud

response = (
    Hudhud()
    .scout("Murata BLM18PG121SN1D datasheet")
    .via("google_cse")              # Primary choice
    .fallback_to("tavily")          # Secondary choice
    .fallback_to("duckduckgo")      # Free fail-safe
    .allow_domains(["murata.com", "mouser.com", "digikey.com"])
    .exclude_domains(["pinterest.com", "facebook.com"])
    .limit(5)
    .with_cache(ttl_seconds=86400)  # Cache results for 24 hours
    .fly()
)

if response:
    print(f"Found {len(response)} results in {response.duration_ms:.1f}ms via {response.provider_used}")
    print(f"Top URL: {response.first().url}")
```

### 3. Asynchronous Execution

```python
import asyncio
from hudhud import Hudhud

async def main():
    response = await (
        Hudhud()
        .scout("Quantum Computing algorithms")
        .via("tavily")
        .fallback_to("duckduckgo")
        .limit(3)
        .fly_async()
    )
    for r in response:
        print(r.title, r.url)

asyncio.run(main())
```

---

## 🏛️ Architecture & Core Philosophy

Hudhud is crafted according to **Eskil Steenberg's principles for building large-scale systems that last decades**:

> *"It's faster to write five lines of code today than to write one line today and then have to edit it in the future."*

```
                       ┌─────────────────────────┐
                       │   Hudhud Fluent API     │
                       └────────────┬────────────┘
                                    │ SearchQuery (Primitive)
                                    ▼
                       ┌─────────────────────────┐
                       │   SearchCache (Protocol)│  <─── SQLite / Memory
                       └────────────┬────────────┘
                                    │ Cache Miss
                                    ▼
                       ┌─────────────────────────┐
                       │ SearchProvider(Protocol)│
                       └──────┬─────┬─────┬──────┘
                              │     │     │
         ┌────────────────────┘     │     └────────────────────┐
         ▼                          ▼                          ▼
  [ Google CSE ]             [   Tavily   ]             [ DuckDuckGo ]
         │                          │                          │
         └────────────────────┬─────┴──────────────────────────┘
                              ▼
                       ┌─────────────────────────┐
                       │ SearchResponse(Primitive│
                       └─────────────────────────┘
```

1. **Primitives**: Pure standard Python `@dataclass(frozen=True)` types.
   - `SearchQuery`: Text, limit, whitelisted domains, blacklisted domains, timeouts.
   - `SearchResult`: Title, url, snippet, provider, rank, score.
   - `SearchResponse`: Immutable container supporting iteration, indexing, and rich metadata.
2. **Black Box Protocols**:
   - `SearchProvider`: `search(query: SearchQuery) -> list[SearchResult]`
   - `SearchCache`: `get(query, provider)` and `set(query, provider, results, ttl)`
3. **Replaceable Components**: Any provider or cache backend can be completely rewritten or replaced without touching the calling code or other providers.

---

## ⚙️ Configuration & Environment Variables

Hudhud automatically reads API keys from system environment variables or a `.env` file:

| Variable | Engine | Description |
| :--- | :--- | :--- |
| `GOOGLE_CSE_API_KEY` | Google CSE | Google Custom Search API Key |
| `GOOGLE_CSE_CX` | Google CSE | Google Custom Search Engine ID |
| `SERP_API_KEY` | SerpAPI | SerpAPI Google Search Key |
| `TAVILY_API_KEY` | Tavily | Tavily AI Search Key |
| `FIRECRAWL_API_KEY` | Firecrawl | Firecrawl API Key |
| `JINA_API_KEY` | Jina | Jina AI Search Key |
| *(None needed)* | DuckDuckGo | Open web scraping via `ddgs` |

You can also pass keys explicitly in code:
```python
from hudhud import Hudhud

response = (
    Hudhud()
    .scout("STMicroelectronics STM32F401")
    .via("google_cse", api_key="AIzaSy...", cx="0175...")
    .fallback_to("tavily", api_key="tvly-...")
    .fly()
)
```

---

## 🧪 Running Tests

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest --cov=hudhud tests/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

