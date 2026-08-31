"""Visualization models, services, and export helpers."""

from __future__ import annotations

import json
import logging
import math
import struct
import zlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from aihw_bench.domain.errors import ReportError
from aihw_bench.domain.models import (
    BenchmarkSession,
    ExecutionPhase,
    ExecutionResult,
    ExecutionStatus,
)
from aihw_bench.domain.ports import Visualizer
from aihw_bench.utils.hashing import sha256_file
from aihw_bench.utils.paths import ensure_directory, resolve_within

VISUALIZATION_DOC = "docs/developer-guide/visualization.md"


@dataclass(frozen=True, slots=True)
class ChartTrace:
    """One data series in a chart specification."""

    name: str
    x: list[Any]
    y: list[float]
    mode: str = "lines+markers"
    chart_type: str = "scatter"

    def to_dict(self) -> dict[str, Any]:
        """Return a Plotly-compatible trace dictionary."""
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "mode": self.mode,
            "type": self.chart_type,
        }


@dataclass(frozen=True, slots=True)
class ChartSpec:
    """Dashboard-ready chart specification."""

    chart_id: str
    title: str
    family: str
    x_axis: str
    y_axis: str
    traces: list[ChartTrace]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable chart specification."""
        return {
            "chart_id": self.chart_id,
            "title": self.title,
            "family": self.family,
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "traces": [trace.to_dict() for trace in self.traces],
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class ChartComponent:
    """Embeddable dashboard/report component."""

    chart_id: str
    title: str
    family: str
    spec: dict[str, Any]
    html: str

    def to_dict(self) -> dict[str, Any]:
        """Return a dashboard-ready component payload."""
        return {
            "chart_id": self.chart_id,
            "title": self.title,
            "family": self.family,
            "spec": self.spec,
            "html": self.html,
        }


@dataclass(frozen=True, slots=True)
class ChartArtifact:
    """Generated chart artifact metadata."""

    chart_id: str
    format: str
    path: Path
    sha256: str


class ChartExportService:
    """Export chart specifications to HTML, SVG, and PNG."""

    def export(
        self,
        spec: ChartSpec,
        output_dir: Path,
        *,
        formats: Sequence[str] = ("html", "svg", "png"),
    ) -> list[ChartArtifact]:
        """Write chart artifacts and return checksum metadata."""
        root = ensure_directory(output_dir)
        artifacts: list[ChartArtifact] = []
        for export_format in tuple(
            dict.fromkeys(format_name.strip().lower() for format_name in formats)
        ):
            payload = self.render(spec, export_format)
            suffix = "html" if export_format == "html" else export_format
            path = resolve_within(root, root / f"{spec.chart_id}.{suffix}")
            if export_format == "png":
                path.write_bytes(payload)
            else:
                path.write_text(payload.decode("utf-8"), encoding="utf-8")
            artifacts.append(
                ChartArtifact(
                    chart_id=spec.chart_id,
                    format=export_format,
                    path=path,
                    sha256=sha256_file(path),
                )
            )
        return artifacts

    def render(self, spec: ChartSpec, export_format: str) -> bytes:
        """Render a chart specification to one supported format."""
        normalized = export_format.strip().lower()
        if normalized == "html":
            return self.render_html(spec).encode("utf-8")
        if normalized == "svg":
            return self.render_svg(spec).encode("utf-8")
        if normalized == "png":
            return self.render_png(spec)
        raise ReportError(
            "Chart export format is not supported.",
            cause=f"Format {export_format!r} is not registered.",
            suggestion="Choose html, svg, or png.",
            documentation=VISUALIZATION_DOC,
        )

    def render_html(self, spec: ChartSpec) -> str:
        """Render an interactive Plotly-compatible HTML fragment."""
        div_id = f"chart-{spec.chart_id}"
        traces = _json_for_html([trace.to_dict() for trace in spec.traces])
        layout = _json_for_html(
            {
                "title": spec.title,
                "xaxis": {"title": spec.x_axis},
                "yaxis": {"title": spec.y_axis},
                "margin": {"t": 48, "r": 24, "b": 48, "l": 64},
            },
        )
        return (
            f'<section class="aihw-chart" data-chart-id="{escape(spec.chart_id, quote=True)}">'
            f"<h3>{escape(spec.title)}</h3>"
            f'<div id="{escape(div_id, quote=True)}"></div>'
            "<script>"
            f"Plotly.newPlot({json.dumps(div_id)}, {traces}, {layout}, {{responsive: true}});"
            "</script>"
            "</section>"
        )

    def render_svg(self, spec: ChartSpec) -> str:
        """Render a deterministic static SVG fallback."""
        width = 720
        height = 360
        margin = 48
        values = [value for trace in spec.traces for value in trace.y]
        upper = max(values) if values else 1.0
        lower = min(values) if values else 0.0
        span = upper - lower or 1.0
        polylines: list[str] = []
        for index, trace in enumerate(spec.traces):
            color = ["#2563eb", "#16a34a", "#dc2626", "#9333ea"][index % 4]
            points: list[str] = []
            count = max(len(trace.y) - 1, 1)
            for point_index, value in enumerate(trace.y):
                x = margin + (point_index / count) * (width - (margin * 2))
                y = height - margin - ((value - lower) / span) * (height - (margin * 2))
                points.append(f"{x:.2f},{y:.2f}")
            joined_points = " ".join(points)
            polylines.append(
                f'<polyline fill="none" stroke="{color}" '
                f'stroke-width="2" points="{joined_points}" />'
            )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            '<rect width="100%" height="100%" fill="#ffffff" />'
            f'<text x="{margin}" y="28" font-family="Arial" font-size="18">'
            f"{escape(spec.title)}</text>"
            f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" '
            f'y2="{height - margin}" stroke="#111827" />'
            f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" '
            f'stroke="#111827" />'
            f'{"".join(polylines)}'
            "</svg>"
        )

    def render_png(self, spec: ChartSpec) -> bytes:
        """Render a small valid PNG preview for artifact pipelines."""
        _ = spec
        return self._blank_png()

    @staticmethod
    def _blank_png() -> bytes:
        width = 1
        height = 1
        raw = b"\x00\xff\xff\xff"
        compressor = zlib.compressobj()
        data = compressor.compress(raw) + compressor.flush()

        def chunk(kind: bytes, payload: bytes) -> bytes:
            checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
            return struct.pack("!I", len(payload)) + kind + payload + struct.pack("!I", checksum)

        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", data)
            + chunk(b"IEND", b"")
        )


class VisualizationService:
    """Build chart specifications and dashboard components from benchmark sessions."""

    def __init__(
        self,
        visualizers: Sequence[Visualizer],
        *,
        exporter: ChartExportService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._visualizers = {visualizer.family: visualizer for visualizer in visualizers}
        self.exporter = exporter or ChartExportService()
        self.logger = logger or logging.getLogger("aihw_bench.visualization")

    def build_specs(
        self,
        session: BenchmarkSession,
        *,
        families: Sequence[str] | None = None,
    ) -> list[ChartSpec]:
        """Build chart specifications for the requested chart families."""
        selected = tuple(families or self._visualizers)
        specs: list[ChartSpec] = []
        for family in selected:
            visualizer = self._resolve_visualizer(family)
            spec = visualizer.build(session)
            self._validate_spec(spec)
            specs.append(spec)
        return specs

    def build_dashboard_components(
        self,
        session: BenchmarkSession,
        *,
        families: Sequence[str] | None = None,
    ) -> list[ChartComponent]:
        """Build HTML components suitable for reports or dashboard shells."""
        return [
            ChartComponent(
                chart_id=spec.chart_id,
                title=spec.title,
                family=spec.family,
                spec=spec.to_dict(),
                html=self.exporter.render_html(spec),
            )
            for spec in self.build_specs(session, families=families)
        ]

    def export(
        self,
        session: BenchmarkSession,
        output_dir: Path,
        *,
        chart_formats: Sequence[str] = ("html", "svg", "png"),
        families: Sequence[str] | None = None,
    ) -> list[ChartArtifact]:
        """Export chart artifacts for the requested session."""
        artifacts: list[ChartArtifact] = []
        for spec in self.build_specs(session, families=families):
            artifacts.extend(self.exporter.export(spec, output_dir, formats=chart_formats))
        return artifacts

    def _resolve_visualizer(self, family: str) -> Visualizer:
        try:
            return self._visualizers[family]
        except KeyError as exc:
            raise ReportError(
                "Chart family is not supported.",
                cause=f"No visualizer is registered for {family!r}.",
                suggestion="Choose one of: " + ", ".join(sorted(self._visualizers)),
                documentation=VISUALIZATION_DOC,
            ) from exc

    @staticmethod
    def _validate_spec(spec: ChartSpec) -> None:
        if not spec.chart_id or not spec.title or not spec.family:
            raise ReportError(
                "Chart specification is invalid.",
                cause="Chart ID, title, and family are required.",
                suggestion="Return a complete ChartSpec from the visualizer.",
                documentation=VISUALIZATION_DOC,
            )
        if not spec.traces:
            raise ReportError(
                "Chart specification has no traces.",
                cause=f"Chart {spec.chart_id!r} does not contain data series.",
                suggestion="Return at least one trace, even for unavailable data.",
                documentation=VISUALIZATION_DOC,
            )


def stable_chart_id(session_id: str, family: str) -> str:
    """Return a stable chart identifier for session and family."""
    return str(uuid5(NAMESPACE_URL, f"aihw-bench:{session_id}:{family}"))


def numeric_metric(session: BenchmarkSession, name: str) -> float | None:
    """Return a numeric metric value by name."""
    for metric in session.metrics:
        if metric.name == name and isinstance(metric.value, int | float):
            return float(metric.value)
    return None


def measured_runs(session: BenchmarkSession) -> list[ExecutionResult]:
    """Return successful measured execution results."""
    return [
        run
        for run in session.runs
        if run.phase is ExecutionPhase.MEASUREMENT and run.status is ExecutionStatus.SUCCESS
    ]


def finite_or_zero(value: float | None) -> float:
    """Return a finite float or zero when a metric is unavailable."""
    if value is None or not math.isfinite(value):
        return 0.0
    return value


def _json_for_html(value: Any) -> str:
    """Serialize data safely for an inline HTML script element."""
    return json.dumps(value, sort_keys=True).replace("</", "<\\/")
