"""Typed exception hierarchy for AIHW-Bench."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorContext:
    """Structured context attached to expected AIHW-Bench errors.

    Args:
        cause: Human-readable reason the operation failed.
        suggestion: Recommended user or developer action.
        documentation: Optional documentation reference.
    """

    cause: str
    suggestion: str
    documentation: str | None = None


class AihwBenchError(Exception):
    """Base class for expected AIHW-Bench errors."""

    default_suggestion = "Review the operation input and consult the AIHW-Bench documentation."

    def __init__(
        self,
        message: str,
        *,
        cause: str | None = None,
        suggestion: str | None = None,
        documentation: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = ErrorContext(
            cause=cause or message,
            suggestion=suggestion or self.default_suggestion,
            documentation=documentation,
        )

    def __str__(self) -> str:
        parts = [
            self.message,
            f"Cause: {self.context.cause}",
            f"Suggestion: {self.context.suggestion}",
        ]
        if self.context.documentation is not None:
            parts.append(f"Documentation: {self.context.documentation}")
        return " | ".join(parts)


class ConfigurationError(AihwBenchError):
    """Raised when configuration cannot be loaded, merged, or validated."""

    default_suggestion = "Fix the configuration source and rerun the command."


class ValidationError(AihwBenchError):
    """Raised when input violates a domain or schema invariant."""

    default_suggestion = "Correct the invalid value before continuing."


class BackendError(AihwBenchError):
    """Raised by backend providers for capability or runtime failures."""


class RuntimeExecutionError(AihwBenchError):
    """Raised when workload execution fails after validation."""


class ModelError(AihwBenchError):
    """Raised when model loading, validation, or metadata extraction fails."""

    default_suggestion = (
        "Use a supported model format and install the required optional runtime dependency."
    )


class ProfilerError(AihwBenchError):
    """Raised when profiler setup or sampling fails."""


class MetricError(AihwBenchError):
    """Raised when metrics cannot be computed or compared safely."""


class PluginError(AihwBenchError):
    """Raised when plugin discovery, validation, or registration fails."""


class SessionError(AihwBenchError):
    """Raised when session persistence or lifecycle rules are violated."""

    default_suggestion = "Inspect the session path and session state before retrying."


class ReportError(AihwBenchError):
    """Raised when report generation fails."""


class ExportError(AihwBenchError):
    """Raised when export artifact generation fails."""


class SecurityError(AihwBenchError):
    """Raised when an operation violates a security boundary."""

    default_suggestion = "Use paths and inputs inside the configured AIHW-Bench workspace."


class InternalError(AihwBenchError):
    """Raised for unexpected internal failures that should be reported."""

    default_suggestion = "Open an issue with the command, environment, and safe diagnostic details."
