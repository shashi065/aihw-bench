"""Clock helpers used by core infrastructure."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def monotonic_seconds() -> float:
    """Return a monotonic high-resolution timestamp in seconds."""
    return perf_counter()
