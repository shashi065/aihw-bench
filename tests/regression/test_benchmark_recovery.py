from __future__ import annotations

from pathlib import Path

from tests.conftest import FakeBackend, FakeHardwareInspector

from aihw_bench.application import BenchmarkRequest, BenchmarkService, ScriptedTimingEngine
from aihw_bench.domain.models import Configuration, ExecutionConfig, ExecutionPhase, SessionStatus
from aihw_bench.infrastructure.storage import FilesystemSessionStore

EXPECTED_PARTIAL_RUNS = 2


def test_partial_session_keeps_successful_measurements_after_later_failure() -> None:
    backend = FakeBackend(
        fail_on={(ExecutionPhase.MEASUREMENT, 1, 0)},
    )
    service = BenchmarkService(
        backend,
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.10, 0.20]),
    )
    request = BenchmarkRequest(
        session_id="partial-session",
        configuration=Configuration(
            execution=ExecutionConfig(warmup_iterations=0, iterations=2, retry_attempts=0),
        ),
    )

    outcome = service.run(request)

    assert outcome.session.status is SessionStatus.PARTIAL
    assert outcome.state.value == "failed"
    assert len(outcome.session.runs) == EXPECTED_PARTIAL_RUNS
    assert outcome.session.runs[0].status.value == "success"
    assert outcome.session.runs[1].status.value == "failed"
    assert outcome.statistics["count"] == 1.0
    assert outcome.session.diagnostics[0].code == "benchmark.execution_failed"


def test_cleanup_failure_downgrades_completed_session_to_partial() -> None:
    backend = FakeBackend(cleanup_error=RuntimeError("cleanup exploded"))
    service = BenchmarkService(
        backend,
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.10]),
    )

    outcome = service.run(
        BenchmarkRequest(
            session_id="cleanup-session",
            configuration=Configuration(
                execution=ExecutionConfig(warmup_iterations=0, iterations=1),
            ),
        )
    )

    assert outcome.session.status is SessionStatus.PARTIAL
    assert outcome.result.status.value == "failed"
    assert outcome.state.value == "failed"
    assert outcome.session.diagnostics[-1].code == "benchmark.cleanup_failed"


def test_report_failure_does_not_invalidate_benchmark_result() -> None:
    class FailingReportService:
        def generate(self, request):
            raise RuntimeError("report writer unavailable")

    service = BenchmarkService(
        FakeBackend(),
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.10]),
        report_service=FailingReportService(),
    )

    outcome = service.run(
        BenchmarkRequest(
            session_id="report-failure-session",
            configuration=Configuration(
                execution=ExecutionConfig(warmup_iterations=0, iterations=1),
            ),
        )
    )

    assert outcome.session.status is SessionStatus.COMPLETED
    assert outcome.result.status.value == "success"


def test_failed_prepare_is_persisted_as_failed_session(tmp_path: Path) -> None:
    store = FilesystemSessionStore(tmp_path)
    service = BenchmarkService(
        FakeBackend(prepare_error=RuntimeError("prepare unavailable")),
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.10]),
        session_store=store,
    )

    outcome = service.run(
        BenchmarkRequest(
            session_id="prepare-failure",
            configuration=Configuration(
                execution=ExecutionConfig(warmup_iterations=0, iterations=1),
            ),
        )
    )

    assert outcome.session.status is SessionStatus.FAILED
    assert outcome.session.diagnostics[0].code == "benchmark.execution_failed"
    assert store.load("prepare-failure").status is SessionStatus.FAILED
