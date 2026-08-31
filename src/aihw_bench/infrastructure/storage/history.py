"""Reliable SQLite benchmark-history index for local deployments."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from aihw_bench.domain.models import BenchmarkSession

_SCHEMA_VERSION = 1
_BUSY_TIMEOUT_MS = 5_000
_RETRY_DELAYS = (0.02, 0.05, 0.1)


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    session_id: str
    created_at: str
    status: str
    backend: str
    device: str
    latency_mean_seconds: float | None


class SqliteHistoryStore:
    """Index immutable sessions using a versioned, local SQLite schema.

    Each operation opens a short-lived connection, enables WAL where supported,
    and retries transient lock contention. The store intentionally remains local
    and does not replace a multi-user database service.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        try:
            connection = sqlite3.connect(self.path, timeout=_BUSY_TIMEOUT_MS / 1000)
            connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
            connection.commit()
        except sqlite3.DatabaseError as exc:
            raise RuntimeError(f"History database is unavailable: {exc}") from exc
        finally:
            if "connection" in locals():
                connection.close()

    def _execute(self, statement: str, values: tuple[object, ...]) -> None:
        for delay in (*_RETRY_DELAYS, None):
            try:
                with self._connection() as connection:
                    connection.execute(statement, values)
                return
            except RuntimeError as exc:
                if "locked" not in str(exc).lower() or delay is None:
                    raise
                time.sleep(delay)

    def index(self, session: BenchmarkSession) -> None:
        """Insert or update a session atomically by immutable session identifier."""
        latency = next(
            (metric.value for metric in session.metrics if metric.name == "latency_mean_seconds"),
            None,
        )
        self._execute(
            """INSERT INTO benchmark_history
               (session_id, created_at, status, backend, device, latency_mean_seconds)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
                 created_at=excluded.created_at, status=excluded.status,
                 backend=excluded.backend, device=excluded.device,
                 latency_mean_seconds=excluded.latency_mean_seconds""",
            (
                session.session_id,
                session.created_at.isoformat(),
                session.status.value,
                session.backend.get("name", session.configuration.backend.name),
                session.configuration.backend.device,
                latency,
            ),
        )

    def query(
        self, *, backend: str | None = None, device: str | None = None, limit: int = 200
    ) -> list[HistoryRecord]:
        """Return a bounded, newest-first history page."""
        if limit <= 0:
            raise ValueError("limit must be positive")
        clauses: list[str] = []
        values: list[object] = []
        if backend:
            clauses.append("backend = ?")
            values.append(backend)
        if device:
            clauses.append("device = ?")
            values.append(device)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        query = (
            "SELECT session_id, created_at, status, backend, device, latency_mean_seconds "
            "FROM benchmark_history" + where + " ORDER BY created_at DESC LIMIT ?"
        )
        values.append(limit)
        with self._connection() as connection:
            rows = connection.execute(query, values).fetchall()
        return [HistoryRecord(*row) for row in rows]

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS history_schema " "(version INTEGER NOT NULL)"
            )
            row = connection.execute("SELECT version FROM history_schema LIMIT 1").fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO history_schema (version) VALUES (?)", (_SCHEMA_VERSION,)
                )
            elif row[0] != _SCHEMA_VERSION:
                raise RuntimeError(
                    f"Unsupported history database schema version {row[0]}; "
                    f"expected {_SCHEMA_VERSION}."
                )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS benchmark_history ("
                "session_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL, "
                "backend TEXT NOT NULL, device TEXT NOT NULL, latency_mean_seconds REAL)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_benchmark_history_filters "
                "ON benchmark_history (backend, device, created_at DESC)"
            )
