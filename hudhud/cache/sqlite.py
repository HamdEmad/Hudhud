"""
SQLite persistent disk cache implementation for Hudhud search queries.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional, Sequence

from hudhud.cache import deserialize_results, make_cache_key, serialize_results
from hudhud.interfaces import SearchCache
from hudhud.primitives import SearchQuery, SearchResult


class SqliteCache(SearchCache):
    """
    Persistent SQLite-backed cache with automatic table creation and TTL expiration.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            home = Path.home()
            cache_dir = home / ".hudhud"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(cache_dir / "cache.sqlite")
        else:
            self.db_path = db_path
            p = Path(db_path)
            if p.parent and str(p.parent) != "." and str(p.parent) != "":
                p.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hudhud_cache (
                    cache_key TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    results_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hudhud_cache_expires ON hudhud_cache(expires_at)"
            )
            conn.commit()

    def get(self, query: SearchQuery, provider: str) -> Optional[Sequence[SearchResult]]:
        key = make_cache_key(query, provider)
        now = time.time()

        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT results_json, expires_at FROM hudhud_cache WHERE cache_key = ?",
                (key,),
            )
            row = cur.fetchone()
            if not row:
                return None

            if now > row["expires_at"]:
                # Evict expired record
                conn.execute("DELETE FROM hudhud_cache WHERE cache_key = ?", (key,))
                conn.commit()
                return None

            try:
                return deserialize_results(row["results_json"])
            except Exception:
                return None

    def set(
        self,
        query: SearchQuery,
        provider: str,
        results: Sequence[SearchResult],
        ttl_seconds: int,
    ) -> None:
        key = make_cache_key(query, provider)
        now = time.time()
        expires_at = now + max(1, ttl_seconds)
        json_data = serialize_results(results)

        with self._lock, self._get_connection() as conn:
            # Opportunistic cleanup of expired rows
            conn.execute("DELETE FROM hudhud_cache WHERE expires_at < ?", (now,))
            conn.execute(
                """
                INSERT INTO hudhud_cache (cache_key, query_text, provider, results_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    results_json = excluded.results_json,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (key, query.text, provider, json_data, now, expires_at),
            )
            conn.commit()

    def clear(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute("DELETE FROM hudhud_cache")
            conn.commit()

