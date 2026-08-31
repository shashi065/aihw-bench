from __future__ import annotations

from aihw_bench.application import BenchmarkRequest, BenchmarkService, ScriptedTimingEngine
from aihw_bench.domain.models import Configuration, ExecutionConfig, ExecutionPhase, SessionStatus
from aihw_bench.infrastructure.backends import ReferenceBenchmarkBackend
from aihw_bench.infrastructure.reporting import default_report_service
from aihw_bench.infrastructure.storage import FilesystemSessionStore

EXPECTED_LATENCY_SECONDS = 0.10
EXPECTED_MEMORY_BYTES = 4096
EXPECTED_CPU_PERCENT = 42.0
EXPECTED_GPU_PERCENT = 58.0
EXPECTED_FLOPS_PER_SECOND = 10_000.0


def test_benchmark_service_persists_final_session(tmp_path) -> None:
    store = FilesystemSessionStore(tmp_path)
    backend = ReferenceBenchmarkBackend()
    service = BenchmarkService(
        backend,
        timing_engine=ScriptedTimingEngine([0.02, 0.03]),
        session_store=store,
    )
    request = BenchmarkRequest(
        session_id="integration-session",
        configuration=Configuration(
            execution=ExecutionConfig(warmup_iterations=0, iterations=2),
        ),
    )

    outcome = service.run(request)

    assert outcome.session.status is SessionStatus.COMPLETED
    assert (tmp_path / "integration-session" / "session.json").exists()
    assert store.list_sessions() == ["integration-session"]


def test_benchmark_service_integrates_metrics_for_reporting(tmp_path) -> None:
    class ObservabilityBackend(ReferenceBenchmarkBackend):
        def execute(self, *args, **kwargs):  # type: ignore[override]
            payload = dict(super().execute(*args, **kwargs))
            phase = args[0]
            if phase is ExecutionPhase.MEASUREMENT:
                payload.update(
                    {
                        "memory_peak_bytes": EXPECTED_MEMORY_BYTES,
                        "cpu_utilization_percent": EXPECTED_CPU_PERCENT,
                        "gpu_utilization_percent": EXPECTED_GPU_PERCENT,
                        "flop_count": 1_000,
                    }
                )
            return payload

    store = FilesystemSessionStore(tmp_path)
    service = BenchmarkService(
        ObservabilityBackend(),
        timing_engine=ScriptedTimingEngine([EXPECTED_LATENCY_SECONDS]),
        session_store=store,
    )
    request = BenchmarkRequest(
        session_id="metrics-reporting-session",
        configuration=Configuration(
            execution=ExecutionConfig(warmup_iterations=0, iterations=1, batch_size=2),
        ),
    )

    outcome = service.run(request)
    loaded = store.load("metrics-reporting-session")
    metrics = {metric.name: metric for metric in loaded.metrics}

    assert outcome.result.summary["measurement_count"] == 1
    assert (
        outcome.result.summary["primary_metrics"]["latency_mean_seconds"]
        == EXPECTED_LATENCY_SECONDS
    )
    assert loaded.results[0].summary["measurement_count"] == 1
    assert metrics["memory_max_bytes"].value == EXPECTED_MEMORY_BYTES
    assert metrics["cpu_utilization_mean_percent"].value == EXPECTED_CPU_PERCENT
    assert metrics["gpu_utilization_mean_percent"].value == EXPECTED_GPU_PERCENT
    assert metrics["estimated_flops_per_second"].value == EXPECTED_FLOPS_PER_SECOND


def test_benchmark_service_can_generate_configured_reports(tmp_path) -> None:
    output_dir = tmp_path / "reports"
    service = BenchmarkService(
        ReferenceBenchmarkBackend(),
        timing_engine=ScriptedTimingEngine([0.05]),
        report_service=default_report_service(),
    )
    request = BenchmarkRequest(
        session_id="benchmark-report-session",
        configuration=Configuration(
            execution=ExecutionConfig(warmup_iterations=0, iterations=1),
            reports=Configuration().reports.model_copy(
                update={"formats": ["json", "markdown"], "output_dir": output_dir}
            ),
        ),
    )

    outcome = service.run(request)

    assert outcome.session.status is SessionStatus.COMPLETED
    assert (output_dir / "benchmark-report-session.json").exists()
    assert (output_dir / "benchmark-report-session.md").exists()
