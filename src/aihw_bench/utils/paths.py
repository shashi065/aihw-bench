"""Safe path handling utilities."""

from __future__ import annotations

from pathlib import Path

from aihw_bench.domain.errors import SecurityError


def resolve_within(root: Path, candidate: Path) -> Path:
    """Resolve a path and ensure it stays within a root directory."""
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise SecurityError(
            "Path escapes configured root.",
            cause=f"{resolved_candidate} is outside {resolved_root}.",
            suggestion="Use a path inside the configured AIHW-Bench workspace.",
            documentation="docs/engineering/security-model.md",
        ) from exc
    return resolved_candidate


def ensure_directory(path: Path) -> Path:
    """Create a directory and return its resolved path."""
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()
