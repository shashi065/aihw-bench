"""Report generation services and report view models."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aihw_bench._version import __version__
from aihw_bench.domain.errors import ReportError
from aihw_bench.domain.models import BenchmarkSession, ExportArtifact, SessionStatus
from aihw_bench.domain.ports import Reporter
from aihw_bench.utils.hashing import sha256_file
from aihw_bench.utils.paths import ensure_directory, resolve_within

REPORT_DOC = "docs/developer-guide/reporting.md"


@dataclass(frozen=True, slots=True)
class ReportMetadata:
    """Metadata recorded for every generated report artifact."""

    report_id: str
    session_id: str
    format: str
    generator: str
    generator_version: str
    generated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable metadata dictionary."""
        return {
            "report_id": self.report_id,
            "session_id": self.session_id,
            "format": self.format,
            "generator": self.generator,
            "generator_version": self.generator_version,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ReportView:
    """Canonical report view consumed by all built-in reporters."""

    metadata: ReportMetadata
    session: dict[str, Any]
    benchmark_summary: dict[str, Any]
    hardware_summary: dict[str, Any]
    model_summary: dict[str, Any] | None
    metrics: list[dict[str, Any]]
    charts: list[dict[str, Any]]
    configuration: dict[str, Any]
    diagnostics: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable report view."""
        return {
            "metadata": self.metadata.to_dict(),
            "session": self.session,
            "benchmark_summary": self.benchmark_summary,
            "hardware_summary": self.hardware_summary,
            "model_summary": self.model_summary,
            "metrics": self.metrics,
            "charts": self.charts,
            "configuration": self.configuration,
            "diagnostics": self.diagnostics,
        }


@dataclass(frozen=True, slots=True)
class ReportRequest:
    """Input accepted by the report service."""

    session: BenchmarkSession
    formats: tuple[str, ...] | None = None
    output_dir: Path | None = None


class ReportViewBuilder:
    """Build report-ready summaries from immutable benchmark sessions."""

    def __init__(self, visualization_service: Any | None = None) -> None:
        self.visualization_service = visualization_service

    def build(self, session: BenchmarkSession, *, report_format: str) -> ReportView:
        """Create a report view for one output format."""
        self._validate_session(session)
        result = session.results[0] if session.results else None
        summary = dict(result.summary if result is not None else {})
        metadata = ReportMetadata(
            report_id=f"{session.session_id}-{report_format}",
            session_id=session.session_id,
            format=report_format,
            generator="aihw-bench",
            generator_version=__version__,
            generated_at=datetime.now(UTC),
        )
        return ReportView(
            metadata=metadata,
            session={
                "session_id": session.session_id,
                "schema_version": session.schema_version,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "completed_at": (
                    session.completed_at.isoformat() if session.completed_at is not None else None
                ),
            },
            benchmark_summary=self._benchmark_summary(session, summary),
            hardware_summary=self._hardware_summary(session),
            model_summary=session.workload.summary() if session.workload is not None else None,
            metrics=[metric.model_dump(mode="json") for metric in session.metrics],
            charts=self._charts(session),
            configuration=session.configuration.model_dump(mode="json"),
            diagnostics=[diagnostic.model_dump(mode="json") for diagnostic in session.diagnostics],
        )

    def build_many(
        self,
        session: BenchmarkSession,
        *,
        report_formats: Sequence[str],
    ) -> list[ReportView]:
        """Build views for several formats while materializing shared content once."""
        if not report_formats:
            return []
        first_format, *remaining_formats = report_formats
        first_view = self.build(session, report_format=first_format)
        return [
            first_view,
            *[
                replace(
                    first_view,
                    metadata=ReportMetadata(
                        report_id=f"{session.session_id}-{report_format}",
                        session_id=session.session_id,
                        format=report_format,
                        generator=first_view.metadata.generator,
                        generator_version=first_view.metadata.generator_version,
                        generated_at=first_view.metadata.generated_at,
                    ),
                )
                for report_format in remaining_formats
            ],
        ]

    @staticmethod
    def _validate_session(session: BenchmarkSession) -> None:
        terminal = {
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
            SessionStatus.PARTIAL,
        }
        if session.status not in terminal:
            raise ReportError(
                "Report generation requires a finalized session.",
                cause=f"Session {session.session_id!r} has status {session.status.value!r}.",
                suggestion="Generate reports after benchmark execution has completed.",
                documentation=REPORT_DOC,
            )

    @staticmethod
    def _benchmark_summary(
        session: BenchmarkSession,
        result_summary: Mapping[str, Any],
    ) -> dict[str, Any]:
        primary_metrics = {
            metric.name: metric.value
            for metric in session.metrics
            if metric.name in {"latency_mean_seconds", "throughput_iterations_per_second"}
        }
        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "backend": session.backend.get("name", session.configuration.backend.name),
            "device": session.configuration.backend.device,
            "precision": session.configuration.execution.precision,
            "batch_size": session.configuration.execution.batch_size,
            "measurement_count": result_summary.get("measurement_count", len(session.runs)),
            "primary_metrics": primary_metrics,
        }

    @staticmethod
    def _hardware_summary(session: BenchmarkSession) -> dict[str, Any]:
        return {
            "host_name": session.hardware.host_name,
            "cpu": session.hardware.cpu,
            "memory": session.hardware.memory,
            "gpu": session.hardware.gpu,
            "accelerators": session.hardware.accelerators,
            "driver_versions": session.hardware.driver_versions,
            "thermal_policy": session.hardware.thermal_policy,
            "power_policy": session.hardware.power_policy,
        }

    def _charts(self, session: BenchmarkSession) -> list[dict[str, Any]]:
        if self.visualization_service is None:
            return []
        try:
            return [
                component.to_dict()
                for component in self.visualization_service.build_dashboard_components(session)
            ]
        except Exception as exc:
            raise ReportError(
                "Report chart generation failed.",
                cause=str(exc),
                suggestion="Inspect visualization providers and chart input data.",
                documentation="docs/developer-guide/visualization.md",
            ) from exc


class ReportService:
    """Validate report requests, manage export directories, and write artifacts."""

    def __init__(
        self,
        reporters: Sequence[Reporter],
        *,
        view_builder: ReportViewBuilder | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._reporters = {reporter.format: reporter for reporter in reporters}
        self._view_builder = view_builder or ReportViewBuilder()
        self._logger = logger or logging.getLogger("aihw_bench.reports")

    def generate(self, request: ReportRequest) -> list[ExportArtifact]:
        """Generate requested report artifacts and return their metadata."""
        formats = self._resolve_formats(request)
        output_dir = self._resolve_output_dir(request)
        artifacts: list[ExportArtifact] = []
        views = self._view_builder.build_many(request.session, report_formats=formats)
        for report_format, view in zip(formats, views, strict=True):
            reporter = self._resolve_reporter(report_format)
            payload = reporter.render(view)
            path = resolve_within(
                output_dir,
                output_dir / f"{request.session.session_id}.{reporter.extension}",
            )
            path.write_text(payload, encoding="utf-8", newline="")
            artifact = ExportArtifact(
                artifact_id=f"{request.session.session_id}-{report_format}",
                kind="report",
                format=report_format,
                path=path,
                sha256=sha256_file(path),
                source_session_ids=[request.session.session_id],
                metadata=view.metadata.to_dict(),
            )
            self._logger.info("Generated %s report at %s", report_format, path)
            artifacts.append(artifact)
        return artifacts

    def _resolve_formats(self, request: ReportRequest) -> tuple[str, ...]:
        requested = request.formats or tuple(request.session.configuration.reports.formats)
        formats = tuple(dict.fromkeys(format_name.strip().lower() for format_name in requested))
        if not formats:
            raise ReportError(
                "No report formats were requested.",
                cause="The report request and configuration did not specify formats.",
                suggestion=(
                    "Request at least one report format such as json, markdown, csv, or html."
                ),
                documentation=REPORT_DOC,
            )
        return formats

    def _resolve_output_dir(self, request: ReportRequest) -> Path:
        output_dir = request.output_dir or request.session.configuration.reports.output_dir
        return ensure_directory(output_dir)

    def _resolve_reporter(self, report_format: str) -> Reporter:
        try:
            return self._reporters[report_format]
        except KeyError as exc:
            raise ReportError(
                "Report format is not supported.",
                cause=f"No reporter is registered for format {report_format!r}.",
                suggestion="Choose one of: " + ", ".join(sorted(self._reporters)),
                documentation=REPORT_DOC,
            ) from exc
