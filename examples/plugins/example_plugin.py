"""Example AIHW-Bench plugin registration."""

from __future__ import annotations

from typing import Any

from aihw_bench.application import (
    ChartSpec,
    ChartTrace,
    PluginManifest,
    PluginProviderKind,
    PluginRegistration,
)
from aihw_bench.domain.models import (
    Configuration,
    ExecutionResult,
    HardwareProfile,
    Metric,
    MetricKind,
    ModelMetadata,
)


class ExampleMetricProvider:
    """Small metric provider suitable for plugin conformance tests."""

    name = "example_plugin_runs"
    version = "0.1.0"
    required_observations: tuple[str, ...] = ()

    def compute(
        self,
        configuration: Configuration,
        runs: tuple[ExecutionResult, ...],
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> tuple[Metric, ...]:
        """Return the number of captured execution runs."""
        return (
            Metric(
                name="example_plugin_runs",
                display_name="Example Plugin Runs",
                value=len(runs),
                unit="runs",
                kind=MetricKind.METADATA,
                source=self.name,
                higher_is_better=None,
            ),
        )


class ExampleMarkdownReporter:
    """Minimal Markdown reporter extension."""

    format = "example-md"
    extension = "md"

    def render(self, view: Any) -> str:
        """Render a compact Markdown report."""
        payload = view.to_dict() if hasattr(view, "to_dict") else dict(view)
        metadata = payload.get("metadata", {})
        return f"# Example Report\n\nSession: `{metadata.get('session_id', 'unknown')}`\n"


class ExampleVisualizer:
    """Minimal dashboard-ready chart extension."""

    family = "example"
    title = "Example Plugin Chart"

    def build(self, session: Any) -> ChartSpec:
        """Build a simple chart from the number of session metrics."""
        metric_count = len(getattr(session, "metrics", ()))
        return ChartSpec(
            chart_id="example-plugin-chart",
            family=self.family,
            title=self.title,
            x_label="category",
            y_label="count",
            traces=(ChartTrace(name="metrics", x=("metrics",), y=(float(metric_count),)),),
        )


def example_cli_command() -> str:
    """Return text that a CLI composition root could expose as a command."""
    return "example plugin command"


def example_exporter(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an export payload annotated with plugin metadata."""
    return {"exported_by": "example-plugin", "payload": payload}


def register_plugin() -> PluginRegistration:
    """Return the example plugin registration."""
    manifest = PluginManifest(
        name="example-plugin",
        version="0.1.0",
        api_version="1.0",
        package="aihw-bench-example-plugin",
        description="Reference plugin demonstrating the Milestone 9 extension API.",
        providers=(
            PluginProviderKind.METRICS,
            PluginProviderKind.REPORTS,
            PluginProviderKind.VISUALIZATIONS,
            PluginProviderKind.CLI_COMMANDS,
            PluginProviderKind.EXPORTERS,
        ),
        capabilities={
            "metrics": ("execution-count",),
            "reports": ("example-md",),
        },
    )
    return PluginRegistration.from_manifest(
        manifest,
        providers={
            PluginProviderKind.METRICS: {"example_plugin_runs": ExampleMetricProvider()},
            PluginProviderKind.REPORTS: {"example-md": ExampleMarkdownReporter()},
            PluginProviderKind.VISUALIZATIONS: {"example": ExampleVisualizer()},
            PluginProviderKind.CLI_COMMANDS: {
                "example": example_cli_command,
            },
            PluginProviderKind.EXPORTERS: {
                "example": example_exporter,
            },
        },
    )
