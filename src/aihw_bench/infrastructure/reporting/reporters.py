"""Concrete report renderers for JSON, CSV, Markdown, and HTML."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, cast

from jinja2 import Environment, Template

from aihw_bench.application.reports import ReportService, ReportView, ReportViewBuilder
from aihw_bench.domain.ports import Reporter
from aihw_bench.infrastructure.reporting.templates import HTML_REPORT_TEMPLATE, MARKDOWN_HEADER
from aihw_bench.infrastructure.visualization import default_visualization_service


@dataclass(frozen=True, slots=True)
class JsonReporter:
    """Render the canonical report view as structured JSON."""

    format: str = "json"
    extension: str = "json"

    def render(self, view: ReportView) -> str:
        """Return a deterministic JSON report."""
        return json.dumps(view.to_dict(), indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True, slots=True)
class CsvReporter:
    """Render metric rows as CSV for spreadsheet and automation workflows."""

    format: str = "csv"
    extension: str = "csv"

    def render(self, view: ReportView) -> str:
        """Return a CSV report containing one row per metric."""
        buffer = io.StringIO()
        fieldnames = [
            "session_id",
            "metric_name",
            "display_name",
            "value",
            "unit",
            "kind",
            "source",
            "higher_is_better",
        ]
        writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for metric in view.metrics:
            writer.writerow(
                {
                    "session_id": view.session["session_id"],
                    "metric_name": metric.get("name"),
                    "display_name": metric.get("display_name"),
                    "value": metric.get("value"),
                    "unit": metric.get("unit"),
                    "kind": metric.get("kind"),
                    "source": metric.get("source"),
                    "higher_is_better": metric.get("higher_is_better"),
                }
            )
        return buffer.getvalue()


@dataclass(frozen=True, slots=True)
class MarkdownReporter:
    """Render a compact Markdown report for pull requests and release notes."""

    format: str = "markdown"
    extension: str = "md"

    def render(self, view: ReportView) -> str:
        """Return a Markdown report."""
        lines = [
            MARKDOWN_HEADER,
            "",
            f"- Session: `{view.session['session_id']}`",
            f"- Status: `{view.session['status']}`",
            f"- Backend: `{view.benchmark_summary.get('backend')}`",
            f"- Device: `{view.benchmark_summary.get('device')}`",
            "",
            "## Benchmark Summary",
            "",
            "| Field | Value |",
            "| --- | --- |",
        ]
        lines.extend(
            f"| `{key}` | {self._format_value(value)} |"
            for key, value in view.benchmark_summary.items()
        )
        lines.extend(
            [
                "",
                "## Metrics",
                "",
                "| Metric | Value | Unit | Kind | Source |",
                "| --- | ---: | --- | --- | --- |",
            ]
        )
        lines.extend(
            "| `{name}` | {value} | {unit} | {kind} | {source} |".format(
                name=metric.get("name"),
                value=self._format_value(metric.get("value")),
                unit=metric.get("unit"),
                kind=metric.get("kind"),
                source=metric.get("source"),
            )
            for metric in view.metrics
        )
        if view.to_dict().get("charts"):
            lines.extend(["", "## Charts", ""])
            lines.extend(
                f"- `{chart['family']}`: {chart['title']}" for chart in view.to_dict()["charts"]
            )
            lines.append("")
        lines.extend(["", "## Hardware Summary", "", "```json"])
        lines.append(json.dumps(view.hardware_summary, indent=2, sort_keys=True))
        lines.extend(["```", "", "## Model Summary", "", "```json"])
        lines.append(json.dumps(view.model_summary, indent=2, sort_keys=True))
        lines.extend(["```", ""])
        return "\n".join(lines)

    @staticmethod
    def _format_value(value: Any) -> str:
        if isinstance(value, dict | list):
            return "`" + json.dumps(value, sort_keys=True) + "`"
        if value is None:
            return "unavailable"
        return str(value)


@dataclass(frozen=True, slots=True)
class HtmlReporter:
    """Render a standalone static HTML report."""

    format: str = "html"
    extension: str = "html"

    def render(self, view: ReportView) -> str:
        """Return a static HTML report."""
        return _html_report_template().render(view=view.to_dict())


def default_reporters() -> tuple[Reporter, ...]:
    """Return all built-in reporters."""
    return cast(
        tuple[Reporter, ...],
        (JsonReporter(), CsvReporter(), MarkdownReporter(), HtmlReporter()),
    )


def default_report_service() -> ReportService:
    """Create a report service with the built-in reporters."""
    return ReportService(
        default_reporters(),
        view_builder=ReportViewBuilder(visualization_service=default_visualization_service()),
    )


@lru_cache(maxsize=1)
def _html_report_template() -> Template:
    """Compile the invariant HTML template once per process."""
    return Environment(autoescape=True).from_string(HTML_REPORT_TEMPLATE)
