from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from aihw_bench.application import (
    ChartExportService,
    ChartSpec,
    ChartTrace,
    ReportViewBuilder,
    VisualizationService,
)
from aihw_bench.domain.errors import ReportError
from aihw_bench.domain.models import (
    BenchmarkSession,
    ExecutionPhase,
    ExecutionResult,
    ExecutionStatus,
    HardwareProfile,
    Metric,
    MetricKind,
    SessionStatus,
)
from aihw_bench.infrastructure.reporting import HtmlReporter, JsonReporter
from aihw_bench.infrastructure.visualization import (
    LatencyVisualizer,
    default_visualization_service,
)

EXPECTED_CHART_FAMILIES = {
    "hardware",
    "latency",
    "memory",
    "performance",
    "roofline",
    "throughput",
    "timeline",
}


def _execution(iteration: int, duration: float) -> ExecutionResult:
    started = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=iteration)
    return ExecutionResult(
        execution_id=f"measurement-{iteration}",
        phase=ExecutionPhase.MEASUREMENT,
        iteration=iteration,
        started_at=started,
        ended_at=started + timedelta(seconds=duration),
        duration_seconds=duration,
        status=ExecutionStatus.SUCCESS,
    )


def _metric(name: str, value: float, unit: str) -> Metric:
    return Metric(
        name=name,
        display_name=name.replace("_", " ").title(),
        value=value,
        unit=unit,
        kind=MetricKind.DERIVED,
        source="metrics-engine",
    )


def _session() -> BenchmarkSession:
    return BenchmarkSession(
        session_id="visual-session",
        hardware=HardwareProfile(
            host_name="host",
            memory={"total_bytes": 8192},
            gpu={"devices": [{"name": "Test GPU"}]},
        ),
        runs=[_execution(0, 0.10), _execution(1, 0.20)],
        metrics=[
            _metric("latency_mean_seconds", 0.15, "seconds"),
            _metric("throughput_iterations_per_second", 6.6, "iterations/s"),
            _metric("throughput_samples_per_second", 13.2, "samples/s"),
            _metric("memory_mean_bytes", 1024, "bytes"),
            _metric("memory_max_bytes", 2048, "bytes"),
            _metric("estimated_flops_per_second", 5000, "FLOP/s"),
        ],
        backend={"name": "reference"},
    ).finalize(SessionStatus.COMPLETED)


def test_default_visualization_service_builds_dashboard_ready_specs() -> None:
    specs = default_visualization_service().build_specs(_session())

    assert {spec.family for spec in specs} == EXPECTED_CHART_FAMILIES
    assert all(spec.chart_id for spec in specs)
    assert all(spec.traces for spec in specs)


def test_visualization_service_builds_components() -> None:
    service = VisualizationService([LatencyVisualizer()])

    components = service.build_dashboard_components(_session())

    assert components[0].family == "latency"
    assert "Plotly.newPlot" in components[0].html
    assert components[0].spec["family"] == "latency"


def test_chart_export_service_writes_html_svg_and_png(tmp_path) -> None:
    spec = ChartSpec(
        chart_id="chart",
        title="Chart",
        family="latency",
        x_axis="iteration",
        y_axis="seconds",
        traces=[ChartTrace(name="latency", x=[0, 1], y=[0.1, 0.2])],
    )

    artifacts = ChartExportService().export(spec, tmp_path)

    assert {artifact.format for artifact in artifacts} == {"html", "png", "svg"}
    assert (tmp_path / "chart.html").read_text(encoding="utf-8").startswith("<section")
    assert (tmp_path / "chart.svg").read_text(encoding="utf-8").startswith("<svg")
    assert (tmp_path / "chart.png").read_bytes().startswith(b"\x89PNG")


def test_chart_rendering_escapes_untrusted_text() -> None:
    spec = ChartSpec(
        chart_id='chart" onmouseover="alert(1)',
        title="</script><script>alert(1)</script>",
        family="latency",
        x_axis="iteration",
        y_axis="seconds",
        traces=[ChartTrace(name="latency", x=[0], y=[0.1])],
    )

    exporter = ChartExportService()

    assert "</script><script>" not in exporter.render_html(spec)
    assert "&lt;/script&gt;" in exporter.render_html(spec)
    assert "</script><script>" not in exporter.render_svg(spec)


def test_visualization_service_rejects_unknown_family() -> None:
    with pytest.raises(ReportError, match="not supported"):
        default_visualization_service().build_specs(_session(), families=("unknown",))


def test_report_view_builder_embeds_chart_components() -> None:
    view = ReportViewBuilder(
        visualization_service=VisualizationService([LatencyVisualizer()])
    ).build(_session(), report_format="html")

    json_payload = JsonReporter().render(view)
    html_payload = HtmlReporter().render(view)

    assert '"charts"' in json_payload
    assert "Latency by Iteration" in html_payload
    assert "Plotly.newPlot" in html_payload
