"""Shared validation helpers for backend implementations."""

from __future__ import annotations

from collections.abc import Iterable

from aihw_bench.domain.errors import BackendError

BACKEND_SUPPORT_DOC = "docs/developer-guide/backend-support.md"


def normalize_backend_token(value: str) -> str:
    """Return a normalized backend capability token."""
    return value.strip().lower()


def validate_precision(
    *,
    backend_name: str,
    supported_precisions: Iterable[str],
    requested_precision: str,
) -> None:
    """Validate that the backend can execute the requested precision."""
    normalized_supported = tuple(
        normalize_backend_token(precision) for precision in supported_precisions
    )
    normalized_requested = normalize_backend_token(requested_precision)
    if normalized_requested in normalized_supported:
        return

    supported_display = ", ".join(normalized_supported)
    raise BackendError(
        "Backend precision is not supported.",
        cause=(
            f"Backend {backend_name!r} supports {supported_display}, "
            f"but {requested_precision!r} was requested."
        ),
        suggestion=(
            "Choose a supported execution precision or select a backend "
            "with the required capability."
        ),
        documentation=BACKEND_SUPPORT_DOC,
    )
