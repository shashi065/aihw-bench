from __future__ import annotations

import json

import pytest

from aihw_bench.application import ReportRequest, ReportService, ReportViewBuilder
from aihw_bench.domain.errors import ReportError
from aihw_bench.domain.models import BenchmarkSession, Metric, MetricKind, SessionStatus
from aihw_bench.infrastructure.reporting import (
    CsvReporter,
    HtmlReporter,
    JsonReporter,
    MarkdownReporter,
    default_report_service,
)


def _session() -> BenchmarkSession:
    metric = Metric(
        name="latency_mean_seconds",
        display_name="Mean Latency",
        value=0.12,
        unit="seconds",
        kind=MetricKind.DERIVED,
        source="metrics-engine",
        higher_is_better=False,
    )
    return BenchmarkSession(
        session_id="report-session",
        metrics=[metric],
        backend={"name": "reference", "version": "1.0.0"},
    ).finalize(SessionStatus.COMPLETED)


def test_report_view_builder_rejects_unfinished_session() -> None:
    with pytest.raises(ReportError, match="finalized session"):
        ReportViewBuilder().build(BenchmarkSession(session_id="draft"), report_format="json")


def test_json_reporter_renders_structured_report() -> None:
    view = ReportViewBuilder().build(_session(), report_format="json")
    payload = json.loads(JsonReporter().render(view))

    assert payload["metadata"]["format"] == "json"
    assert payload["session"]["session_id"] == "report-session"
    assert payload["metrics"][0]["name"] == "latency_mean_seconds"


def test_text_reporters_render_expected_sections() -> None:
    view = ReportViewBuilder().build(_session(), report_format="markdown")

    assert "AIHW-Bench Report" in MarkdownReporter().render(view)
    assert "latency_mean_seconds" in CsvReporter().render(view)
    assert "<html" in HtmlReporter().render(view)


def test_report_service_validates_requested_format(tmp_path) -> None:
    service = ReportService([JsonReporter()])

    with pytest.raises(ReportError, match="not supported"):
        service.generate(ReportRequest(session=_session(), formats=("xml",), output_dir=tmp_path))


def test_report_service_builds_shared_view_once_for_multiple_formats(tmp_path) -> None:
    class CountingViewBuilder(ReportViewBuilder):
        def __init__(self) -> None:
            super().__init__()
            self.build_calls = 0

        def build(self, session, *, report_format):  # type: ignore[no-untyped-def]
            self.build_calls += 1
            return super().build(session, report_format=report_format)

    builder = CountingViewBuilder()
    service = ReportService([JsonReporter(), CsvReporter()], view_builder=builder)

    service.generate(
        ReportRequest(session=_session(), formats=("json", "csv"), output_dir=tmp_path)
    )

    assert builder.build_calls == 1


def test_report_service_writes_all_default_formats(tmp_path) -> None:
    artifacts = default_report_service().generate(
        ReportRequest(
            session=_session(),
            formats=("json", "markdown", "csv", "html"),
            output_dir=tmp_path,
        )
    )

    assert {artifact.format for artifact in artifacts} == {"csv", "html", "json", "markdown"}
    assert all(artifact.path.exists() for artifact in artifacts)
    assert all(artifact.sha256 for artifact in artifacts)
