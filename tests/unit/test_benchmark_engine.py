from __future__ import annotations

import pytest
from tests.conftest import FakeBackend, FakeHardwareInspector

from aihw_bench.application import (
    BenchmarkLifecycleState,
    BenchmarkRequest,
    BenchmarkService,
    ExecutionScheduler,
    MonotonicTimingEngine,
    ScriptedTimingEngine,
    StatisticsEngine,
)
from aihw_bench.application.benchmark import LifecycleTracker
from aihw_bench.domain.errors import RuntimeExecutionError, ValidationError
from aihw_bench.domain.models import (
    Configuration,
    ExecutionConfig,
    ExecutionPhase,
    SessionStatus,
    WorkloadConfig,
)
from aihw_bench.infrastructure.backends import ReferenceBenchmarkBackend
from aihw_bench.infrastructure.storage import FilesystemSessionStore

EXPECTED_STAT_COUNT = 3.0
EXPECTED_FULL_RUNS = 3
EXPECTED_MEASURED_COUNT = 2.0
EXPECTED_RETRY_RUNS = 2


def test_execution_scheduler_places_warmup_before_measurement() -> None:
    scheduler = ExecutionScheduler()

    plan = scheduler.plan(warmup_iterations=2, iterations=3)

    assert [(step.phase, step.iteration) for step in plan.steps] == [
        (ExecutionPhase.WARMUP, 0),
        (ExecutionPhase.WARMUP, 1),
        (ExecutionPhase.MEASUREMENT, 0),
        (ExecutionPhase.MEASUREMENT, 1),
        (ExecutionPhase.MEASUREMENT, 2),
    ]
    assert [step.iteration for step in plan.measured_steps] == [0, 1, 2]


def test_execution_scheduler_rejects_invalid_counts() -> None:
    scheduler = ExecutionScheduler()

    with pytest.raises(ValidationError, match="Warmup"):
        scheduler.plan(warmup_iterations=-1, iterations=1)
    with pytest.raises(ValidationError, match="Measured"):
        scheduler.plan(warmup_iterations=0, iterations=0)


def test_statistics_engine_computes_common_summaries() -> None:
    statistics = StatisticsEngine().summarize([0.1, 0.2, 0.4])

    assert statistics["count"] == EXPECTED_STAT_COUNT
    assert statistics["min_seconds"] == pytest.approx(0.1)
    assert statistics["max_seconds"] == pytest.approx(0.4)
    assert statistics["mean_seconds"] == pytest.approx(0.2333333333)
    assert statistics["median_seconds"] == pytest.approx(0.2)
    assert statistics["throughput_iterations_per_second"] == pytest.approx(4.2857142857)


def test_statistics_engine_rejects_empty_measurements() -> None:
    with pytest.raises(ValidationError, match="At least one measured duration"):
        StatisticsEngine().summarize([])


def test_statistics_engine_handles_single_and_zero_duration_samples() -> None:
    statistics = StatisticsEngine().summarize([0.0])

    assert statistics["p95_seconds"] == 0.0
    assert statistics["stdev_seconds"] == 0.0
    assert statistics["throughput_iterations_per_second"] == 0.0

    with pytest.raises(ValidationError, match="percentile"):
        StatisticsEngine._percentile([], 95.0)


def test_lifecycle_tracker_rejects_invalid_transition() -> None:
    tracker = LifecycleTracker()

    with pytest.raises(ValidationError, match="Invalid"):
        tracker.transition(BenchmarkLifecycleState.COMPLETED)


def test_benchmark_service_runs_warmup_and_measured_iterations(tmp_path) -> None:
    backend = ReferenceBenchmarkBackend()
    store = FilesystemSessionStore(tmp_path)
    service = BenchmarkService(
        backend,
        timing_engine=ScriptedTimingEngine([0.01, 0.10, 0.20]),
        session_store=store,
    )
    request = BenchmarkRequest(
        session_id="session-1",
        configuration=Configuration(
            execution=ExecutionConfig(warmup_iterations=1, iterations=2, retry_attempts=0),
        ),
    )

    outcome = service.run(request)

    assert outcome.state.value == "completed"
    assert outcome.session.status is SessionStatus.COMPLETED
    assert len(outcome.session.runs) == EXPECTED_FULL_RUNS
    assert [run.phase for run in outcome.session.runs] == [
        ExecutionPhase.WARMUP,
        ExecutionPhase.MEASUREMENT,
        ExecutionPhase.MEASUREMENT,
    ]
    assert outcome.statistics["count"] == EXPECTED_MEASURED_COUNT
    assert outcome.result.status.value == "success"
    assert outcome.result.primary_metric("latency_mean_seconds") is not None
    assert (tmp_path / "session-1" / "session.json").exists()
    assert backend.calls[0]["operation"] == "prepare"
    assert backend.calls[-1]["operation"] == "cleanup"


def test_benchmark_service_retries_a_failed_measurement() -> None:
    class RetryBackend(ReferenceBenchmarkBackend):
        def __init__(self) -> None:
            super().__init__()
            self.invocations = 0

        def execute(self, *args, **kwargs):  # type: ignore[override]
            self.invocations += 1
            if self.invocations == 1:
                raise RuntimeError("transient failure")
            return super().execute(*args, **kwargs)

    backend = RetryBackend()
    service = BenchmarkService(
        backend,
        timing_engine=ScriptedTimingEngine([0.01, 0.20]),
    )
    request = BenchmarkRequest(
        session_id="session-2",
        configuration=Configuration(
            execution=ExecutionConfig(warmup_iterations=0, iterations=1, retry_attempts=1),
        ),
    )

    outcome = service.run(request)

    assert outcome.session.status is SessionStatus.COMPLETED
    assert outcome.result.status.value == "success"
    assert len(outcome.session.runs) == EXPECTED_RETRY_RUNS
    assert outcome.session.runs[0].status.value == "failed"
    assert outcome.session.runs[1].status.value == "success"


def test_benchmark_service_records_failure_diagnostics() -> None:
    class FailingBackend(ReferenceBenchmarkBackend):
        def execute(self, *args, **kwargs):  # type: ignore[override]
            raise RuntimeError("boom")

    service = BenchmarkService(
        FailingBackend(),
        timing_engine=ScriptedTimingEngine([0.05]),
    )
    request = BenchmarkRequest(
        session_id="session-3",
        configuration=Configuration(
            execution=ExecutionConfig(warmup_iterations=0, iterations=1, retry_attempts=0),
        ),
    )

    outcome = service.run(request)

    assert outcome.session.status in {SessionStatus.FAILED, SessionStatus.PARTIAL}
    assert outcome.result.status.value == "failed"
    assert outcome.session.diagnostics
    assert "boom" in outcome.session.diagnostics[0].cause


def test_benchmark_service_rejects_missing_backend() -> None:
    service = BenchmarkService(hardware_inspector=FakeHardwareInspector())

    with pytest.raises(RuntimeExecutionError, match="No backend"):
        service.run(
            BenchmarkRequest(
                session_id="missing-backend",
                configuration=Configuration(
                    execution=ExecutionConfig(warmup_iterations=0, iterations=1),
                ),
            )
        )


def test_benchmark_service_uses_backend_registry_validation() -> None:
    class Registry:
        def __init__(self) -> None:
            self.validated = False

        def register(self, backend):
            return None

        def resolve(self, name: str):
            raise AssertionError(name)

        def select(self, configuration, hardware, workload=None):
            raise AssertionError("select should not be called")

        def validate(self, backend, configuration, hardware, workload=None):
            self.validated = True

    registry = Registry()
    service = BenchmarkService(
        FakeBackend(),
        backend_registry=registry,
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.05]),
    )

    outcome = service.run(
        BenchmarkRequest(
            session_id="registry-validation",
            configuration=Configuration(
                execution=ExecutionConfig(warmup_iterations=0, iterations=1),
            ),
        )
    )

    assert registry.validated
    assert outcome.session.status is SessionStatus.COMPLETED


def test_benchmark_service_uses_selected_registry_backend() -> None:
    class Registry:
        def __init__(self, backend: FakeBackend) -> None:
            self.backend = backend

        def register(self, backend):
            return None

        def resolve(self, name: str):
            return self.backend

        def select(self, configuration, hardware, workload=None):
            return self.backend

        def validate(self, backend, configuration, hardware, workload=None):
            return None

    backend = FakeBackend()
    service = BenchmarkService(
        backend_registry=Registry(backend),
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.05]),
    )

    outcome = service.run(
        BenchmarkRequest(
            session_id="selected-backend",
            configuration=Configuration(
                execution=ExecutionConfig(warmup_iterations=0, iterations=1),
            ),
        )
    )

    assert outcome.session.backend["name"] == "fake"


def test_benchmark_service_builds_configured_workload_metadata() -> None:
    service = BenchmarkService(
        FakeBackend(),
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.05]),
    )
    configuration = Configuration(
        workload=WorkloadConfig(
            name="configured-demo",
            input_shapes={"input": [1, 4]},
            metadata={"format": "synthetic", "framework": "unit"},
        ),
        execution=ExecutionConfig(warmup_iterations=0, iterations=1),
    )

    outcome = service.run(
        BenchmarkRequest(session_id="configured-workload", configuration=configuration)
    )

    assert outcome.session.workload is not None
    assert outcome.session.workload.format == "synthetic"
    assert outcome.session.workload.input_shapes == {"input": [1, 4]}


def test_benchmark_service_requires_model_catalog_for_workload_source() -> None:
    service = BenchmarkService(
        FakeBackend(),
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.05]),
    )
    configuration = Configuration(
        workload=WorkloadConfig(source="model.fake"),
        execution=ExecutionConfig(warmup_iterations=0, iterations=1),
    )

    outcome = service.run(
        BenchmarkRequest(session_id="missing-catalog", configuration=configuration)
    )

    assert outcome.session.status is SessionStatus.FAILED
    assert "model catalog" in outcome.session.diagnostics[0].cause


def test_benchmark_service_marks_timeout_as_failed_measurement() -> None:
    service = BenchmarkService(
        FakeBackend(),
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.50]),
    )
    configuration = Configuration(
        execution=ExecutionConfig(warmup_iterations=0, iterations=1, timeout_seconds=0.1),
    )

    outcome = service.run(
        BenchmarkRequest(session_id="timeout-session", configuration=configuration)
    )

    assert outcome.session.status is SessionStatus.FAILED
    assert "timeout" in outcome.session.runs[0].error.lower()


def test_monotonic_timing_engine_measures_callable() -> None:
    sample = MonotonicTimingEngine().measure(lambda: "ok")

    assert sample.value == "ok"
    assert sample.duration_seconds >= 0
    assert sample.ended_at >= sample.started_at
