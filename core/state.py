"""
Pi Agent — State Persistence Engine
====================================
SQLite-based session persistence untuk Pi Agent.
Mengadaptasi pola state serialization dari Google agents-cli / ADK 2.0.

Fitur:
  - Auto-save session state ke SQLite
  - Resume session dari disk
  - Session history dengan metadata
  - Background worker mode (suspend/resume)

Usage:
    from state import SessionStore
    store = SessionStore()
    store.save("last_task", {"workflow": "coding", "prompt": "..."})
    last = store.load("last_task")
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ── Constants ──────────────────────────────────────────────────────────────────

STATE_DIR = Path.home() / ".pi" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = STATE_DIR / "sessions.db"


# ── Session Store ──────────────────────────────────────────────────────────────

class SessionStore:
    """
    Persistent key-value store with session history.

    Tables:
      - kv_store:     key → JSON value (general purpose)
      - sessions:     conversation/session log
      - eval_results: benchmark result cache

    Auto-creates database and tables on first use.
    """

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                workflow    TEXT,
                model       TEXT,
                prompt      TEXT,
                response    TEXT,
                latency_ms  INTEGER,
                score       REAL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_session_id
                ON sessions(session_id);

            CREATE INDEX IF NOT EXISTS idx_sessions_created
                ON sessions(created_at);
        """)
        self._conn.commit()

    # ── KV Store ──────────────────────────────────────────────────────────

    def save(self, key: str, value: Any) -> None:
        """Save any JSON-serializable value by key."""
        self._conn.execute(
            "INSERT OR REPLACE INTO kv_store (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (key, json.dumps(value, default=str)),
        )
        self._conn.commit()

    def load(self, key: str, default: Any = None) -> Any:
        """Load value by key. Return default if not found."""
        row = self._conn.execute(
            "SELECT value FROM kv_store WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    def delete(self, key: str) -> None:
        """Delete a key."""
        self._conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
        self._conn.commit()

    def keys(self, pattern: Optional[str] = None) -> list[str]:
        """List all keys, optionally matching SQL LIKE pattern."""
        if pattern:
            rows = self._conn.execute(
                "SELECT key FROM kv_store WHERE key LIKE ?", (pattern,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT key FROM kv_store").fetchall()
        return [r["key"] for r in rows]

    # ── Session Log ───────────────────────────────────────────────────────

    def log_session(
        self,
        session_id: str,
        workflow: str,
        model: str,
        prompt: str,
        response: str,
        latency_ms: int = 0,
        score: Optional[float] = None,
    ) -> int:
        """Log a session interaction. Returns row ID."""
        cur = self._conn.execute(
            """INSERT INTO sessions (session_id, workflow, model, prompt, response, latency_ms, score)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, workflow, model, prompt[:8000], response[:8000], latency_ms, score),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_sessions(
        self,
        limit: int = 50,
        workflow: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> list[dict]:
        """Get session history, newest first."""
        query = "SELECT * FROM sessions WHERE 1=1"
        params = []
        if workflow:
            query += " AND workflow = ?"
            params.append(workflow)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_recent_workflows(self, limit: int = 10) -> list[str]:
        """Get most recent workflows used."""
        rows = self._conn.execute(
            """SELECT DISTINCT workflow FROM sessions
               WHERE workflow IS NOT NULL
               ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [r["workflow"] for r in rows]

    # ── Eval Cache ────────────────────────────────────────────────────────

    def cache_eval(self, task_id: str, model: str, data: dict) -> None:
        """Cache eval result for a task+model combo."""
        self.save(f"eval:{task_id}:{model}", data)

    def get_cached_eval(self, task_id: str, model: str) -> Optional[dict]:
        """Get cached eval result."""
        return self.load(f"eval:{task_id}:{model}")

    # ── Stats ─────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        """Database statistics."""
        kv_count = self._conn.execute("SELECT COUNT(*) as c FROM kv_store").fetchone()["c"]
        session_count = self._conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        return {
            "kv_entries": kv_count,
            "sessions": session_count,
            "db_size_bytes": db_size,
            "db_path": str(self.db_path),
        }

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def close(self):
        """Close database connection."""
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ── Quick Test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    store = SessionStore()

    if "--test" in sys.argv:
        print("🔍 Testing SessionStore...")

        # KV store
        store.save("test_key", {"hello": "world", "number": 42})
        val = store.load("test_key")
        assert val == {"hello": "world", "number": 42}, f"Got {val}"
        print("  ✅ KV store works")

        # Session log
        sid = store.log_session(
            session_id="test-session-123",
            workflow="coding",
            model="Qwopus3.5-4B",
            prompt="Buat fungsi fibonacci",
            response="def fib(n):...",
            latency_ms=26500,
            score=8.5,
        )
        assert sid > 0
        sessions = store.get_sessions(limit=5)
        assert len(sessions) >= 1
        print("  ✅ Session log works")

        # Workflows
        wfs = store.get_recent_workflows()
        assert "coding" in wfs
        print("  ✅ Workflow tracking works")

        # Stats
        s = store.stats
        print(f"  ✅ Stats: {s['kv_entries']} kv, {s['sessions']} sessions, {s['db_size_bytes']} bytes")

        # Cleanup test data
        store.delete("test_key")
        print("  ✅ All tests passed!")
