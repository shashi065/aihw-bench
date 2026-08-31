"""Built-in chart providers for benchmark sessions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aihw_bench.application.visualization import (
    ChartSpec,
    ChartTrace,
    VisualizationService,
    finite_or_zero,
    measured_runs,
    numeric_metric,
    stable_chart_id,
)
from aihw_bench.domain.models import BenchmarkSession


@dataclass(frozen=True, slots=True)
class LatencyVisualizer:
    """Build per-iteration latency charts."""

    family: str = "latency"
    title: str = "Latency by Iteration"

    def build(self, session: BenchmarkSession) -> ChartSpec:
        """Return a latency line chart."""
        runs = measured_runs(session)
        return ChartSpec(
            chart_id=stable_chart_id(session.session_id, self.family),
            title=self.title,
            family=self.family,
            x_axis="iteration",
            y_axis="seconds",
            traces=[
                ChartTrace(
                    name="latency",
                    x=[run.iteration for run in runs] or [0],
                    y=[run.duration_seconds for run in runs] or [0.0],
                )
            ],
            metadata={"dashboard_component": "line-chart"},
        )


@dataclass(frozen=True, slots=True)
class ThroughputVisualizer:
    """Build throughput summary charts."""

    family: str = "throughput"
    title: str = "Throughput Summary"

    def build(self, session: BenchmarkSession) -> ChartSpec:
        """Return a throughput bar chart."""
        return ChartSpec(
            chart_id=stable_chart_id(session.session_id, self.family),
            title=self.title,
            family=self.family,
            x_axis="metric",
            y_axis="rate",
            traces=[
                ChartTrace(
                    name="throughput",
                    x=["iterations/s", "samples/s"],
                    y=[
                        finite_or_zero(numeric_metric(session, "throughput_iterations_per_second")),
                        finite_or_zero(numeric_metric(session, "throughput_samples_per_second")),
                    ],
                    mode="markers",
                    chart_type="bar",
                )
            ],
            metadata={"dashboard_component": "bar-chart"},
        )


@dataclass(frozen=True, slots=True)
class MemoryUsageVisualizer:
    """Build memory usage charts from resource metrics or observations."""

    family: str = "memory"
    title: str = "Memory Usage"

    def build(self, session: BenchmarkSession) -> ChartSpec:
        """Return a memory usage bar chart."""
        return ChartSpec(
            chart_id=stable_chart_id(session.session_id, self.family),
            title=self.title,
            family=self.family,
            x_axis="metric",
            y_axis="bytes",
            traces=[
                ChartTrace(
                    name="memory",
                    x=["mean", "max"],
                    y=[
                        finite_or_zero(numeric_metric(session, "memory_mean_bytes")),
                        finite_or_zero(numeric_metric(session, "memory_max_bytes")),
                    ],
                    mode="markers",
                    chart_type="bar",
                )
            ],
            metadata={"dashboard_component": "bar-chart"},
        )


@dataclass(frozen=True, slots=True)
class TimelineVisualizer:
    """Build execution timeline charts."""

    family: str = "timeline"
    title: str = "Execution Timeline"

    def build(self, session: BenchmarkSession) -> ChartSpec:
        """Return a timeline chart using run start order and durations."""
        runs = list(session.runs)
        return ChartSpec(
            chart_id=stable_chart_id(session.session_id, self.family),
            title=self.title,
            family=self.family,
            x_axis="run",
            y_axis="seconds",
            traces=[
                ChartTrace(
                    name="duration",
                    x=[run.execution_id for run in runs] or ["no-runs"],
                    y=[run.duration_seconds for run in runs] or [0.0],
                    mode="markers",
                    chart_type="bar",
                )
            ],
            metadata={"dashboard_component": "timeline-chart"},
        )


@dataclass(frozen=True, slots=True)
class HardwareComparisonVisualizer:
    """Build hardware context comparison charts."""

    family: str = "hardware"
    title: str = "Hardware Summary"

    def build(self, session: BenchmarkSession) -> ChartSpec:
        """Return a hardware summary chart."""
        memory_total = _numeric(session.hardware.memory.get("total_bytes"))
        gpu_count = len(session.hardware.gpu.get("devices", []) or [])
        accelerator_count = len(session.hardware.accelerators)
        return ChartSpec(
            chart_id=stable_chart_id(session.session_id, self.family),
            title=self.title,
            family=self.family,
            x_axis="resource",
            y_axis="count_or_bytes",
            traces=[
                ChartTrace(
                    name="hardware",
                    x=["memory_bytes", "gpu_count", "accelerator_count"],
                    y=[memory_total, float(gpu_count), float(accelerator_count)],
                    mode="markers",
                    chart_type="bar",
                )
            ],
            metadata={"dashboard_component": "hardware-summary-chart"},
        )


@dataclass(frozen=True, slots=True)
class PerformanceComparisonVisualizer:
    """Build single-session performance comparison charts."""

    family: str = "performance"
    title: str = "Performance Metrics"

    def build(self, session: BenchmarkSession) -> ChartSpec:
        """Return a normalized performance metric chart."""
        return ChartSpec(
            chart_id=stable_chart_id(session.session_id, self.family),
            title=self.title,
            family=self.family,
            x_axis="metric",
            y_axis="value",
            traces=[
                ChartTrace(
                    name="performance",
                    x=["latency", "throughput", "flops"],
                    y=[
                        finite_or_zero(numeric_metric(session, "latency_mean_seconds")),
                        finite_or_zero(numeric_metric(session, "throughput_iterations_per_second")),
                        finite_or_zero(numeric_metric(session, "estimated_flops_per_second")),
                    ],
                    mode="markers",
                    chart_type="bar",
                )
            ],
            metadata={"dashboard_component": "comparison-chart"},
        )


@dataclass(frozen=True, slots=True)
class RooflineFoundationVisualizer:
    """Build a roofline foundation chart from available operation and memory metrics."""

    family: str = "roofline"
    title: str = "Roofline Foundation"

    def build(self, session: BenchmarkSession) -> ChartSpec:
        """Return a foundation chart for later roofline analysis."""
        flops = finite_or_zero(numeric_metric(session, "estimated_flops_per_second"))
        memory = finite_or_zero(numeric_metric(session, "memory_max_bytes"))
        arithmetic_intensity = flops / memory if memory > 0 else 0.0
        return ChartSpec(
            chart_id=stable_chart_id(session.session_id, self.family),
            title=self.title,
            family=self.family,
            x_axis="arithmetic_intensity_flops_per_byte",
            y_axis="FLOP/s",
            traces=[
                ChartTrace(
                    name="workload",
                    x=[arithmetic_intensity],
                    y=[flops],
                    mode="markers",
                )
            ],
            metadata={
                "dashboard_component": "roofline-chart",
                "foundation_only": True,
                "assumptions": [
                    "Uses estimated FLOPS and measured maximum memory bytes when available."
                ],
            },
        )


def default_visualizers() -> tuple[Any, ...]:
    """Return all built-in visualizers."""
    return (
        LatencyVisualizer(),
        ThroughputVisualizer(),
        MemoryUsageVisualizer(),
        HardwareComparisonVisualizer(),
        TimelineVisualizer(),
        PerformanceComparisonVisualizer(),
        RooflineFoundationVisualizer(),
    )


def default_visualization_service() -> VisualizationService:
    """Return the default visualization service."""
    return VisualizationService(default_visualizers())


def _numeric(value: Any) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0
