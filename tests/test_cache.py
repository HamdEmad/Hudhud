"""
Unit tests for Hudhud MemoryCache and SqliteCache implementations.
"""

import time
import pytest
from hudhud.cache.memory import MemoryCache
from hudhud.cache.sqlite import SqliteCache
from hudhud.primitives import SearchQuery, SearchResult


def test_memory_cache_hit_and_miss(sample_query, sample_results):
    cache = MemoryCache()

    # Initial get is a miss
    assert cache.get(sample_query, "google_cse") is None

    # Set results with 10s TTL
    cache.set(sample_query, "google_cse", sample_results, ttl_seconds=10)

    # Cache hit
    cached = cache.get(sample_query, "google_cse")
    assert cached is not None
    assert len(cached) == len(sample_results)
    assert cached[0].title == sample_results[0].title

    # Different provider is a miss
    assert cache.get(sample_query, "tavily") is None


def test_memory_cache_ttl_expiration(sample_query, sample_results):
    cache = MemoryCache()
    # 1 second TTL
    cache.set(sample_query, "google_cse", sample_results, ttl_seconds=1)

    assert cache.get(sample_query, "google_cse") is not None
    time.sleep(1.1)
    assert cache.get(sample_query, "google_cse") is None


def test_memory_cache_clear(sample_query, sample_results):
    cache = MemoryCache()
    cache.set(sample_query, "google_cse", sample_results, ttl_seconds=60)
    assert cache.get(sample_query, "google_cse") is not None

    cache.clear()
    assert cache.get(sample_query, "google_cse") is None


def test_sqlite_cache_persistence_and_hit(tmp_path, sample_query, sample_results):
    db_file = str(tmp_path / "test_cache.sqlite")
    cache = SqliteCache(db_path=db_file)

    # Initial get is a miss
    assert cache.get(sample_query, "google_cse") is None

    # Set results
    cache.set(sample_query, "google_cse", sample_results, ttl_seconds=300)

    # Re-open with new SqliteCache instance pointing to same file
    cache2 = SqliteCache(db_path=db_file)
    cached = cache2.get(sample_query, "google_cse")

    assert cached is not None
    assert len(cached) == len(sample_results)
    assert cached[0].title == sample_results[0].title
    assert cached[0].url == sample_results[0].url
    assert cached[1].snippet == sample_results[1].snippet


def test_sqlite_cache_ttl_expiration(tmp_path, sample_query, sample_results):
    db_file = str(tmp_path / "test_ttl.sqlite")
    cache = SqliteCache(db_path=db_file)

    cache.set(sample_query, "google_cse", sample_results, ttl_seconds=1)
    assert cache.get(sample_query, "google_cse") is not None

    time.sleep(1.1)
    assert cache.get(sample_query, "google_cse") is None


def test_sqlite_cache_clear(tmp_path, sample_query, sample_results):
    db_file = str(tmp_path / "test_clear.sqlite")
    cache = SqliteCache(db_path=db_file)

    cache.set(sample_query, "google_cse", sample_results, ttl_seconds=300)
    assert cache.get(sample_query, "google_cse") is not None

    cache.clear()
    assert cache.get(sample_query, "google_cse") is None

