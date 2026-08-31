from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from aihw_bench.application.metrics import (
    CoreMetricsEngine,
    ResultSerializer,
    StatisticalAggregator,
)
from aihw_bench.domain.errors import ValidationError
from aihw_bench.domain.models import (
    Configuration,
    ExecutionConfig,
    ExecutionPhase,
    ExecutionResult,
    ExecutionStatus,
    HardwareProfile,
    MetricKind,
    ModelMetadata,
)

EXPECTED_SAMPLE_COUNT = 3.0
EXPECTED_MEASUREMENT_COUNT = 2
EXPECTED_MEMORY_MAX_BYTES = 2048


def _run(iteration: int, duration: float, observations: dict[str, object]) -> ExecutionResult:
    started = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=iteration)
    return ExecutionResult(
        execution_id=f"run-{iteration}",
        phase=ExecutionPhase.MEASUREMENT,
        iteration=iteration,
        started_at=started,
        ended_at=started + timedelta(seconds=duration),
        duration_seconds=duration,
        status=ExecutionStatus.SUCCESS,
        observations=observations,
    )


def test_statistical_aggregator_computes_percentiles() -> None:
    summary = StatisticalAggregator().summarize([0.1, 0.2, 0.4])

    assert summary["count"] == EXPECTED_SAMPLE_COUNT
    assert summary["mean"] == pytest.approx(0.2333333333)
    assert summary["p95"] == pytest.approx(0.38)


def test_statistical_aggregator_rejects_empty_samples() -> None:
    with pytest.raises(ValidationError, match="At least one numeric sample"):
        StatisticalAggregator().summarize([])


def test_core_metrics_engine_computes_resource_and_flops_metrics() -> None:
    runs = [
        _run(
            0,
            0.10,
            {
                "memory_peak_bytes": 1024,
                "cpu_utilization_percent": 50.0,
                "gpu_utilization_percent": 70.0,
            },
        ),
        _run(
            1,
            0.20,
            {
                "memory_peak_bytes": 2048,
                "cpu_utilization_percent": 60.0,
                "gpu_utilization_percent": 80.0,
            },
        ),
    ]
    configuration = Configuration(execution=ExecutionConfig(batch_size=4, warmup_iterations=0))
    workload = ModelMetadata(
        model_id="demo",
        name="Demo",
        format="onnx",
        macs=1_000,
    )

    bundle = CoreMetricsEngine().compute(
        session_id="metrics-session",
        configuration=configuration,
        runs=runs,
        hardware=HardwareProfile(cpu={"name": "test-cpu"}),
        workload=workload,
    )
    metrics = {metric.name: metric for metric in bundle.metrics}

    assert metrics["latency_mean_seconds"].value == pytest.approx(0.15)
    assert metrics["throughput_iterations_per_second"].value == pytest.approx(6.6666666667)
    assert metrics["throughput_samples_per_second"].value == pytest.approx(26.6666666667)
    assert metrics["memory_max_bytes"].value == EXPECTED_MEMORY_MAX_BYTES
    assert metrics["cpu_utilization_mean_percent"].value == pytest.approx(55.0)
    assert metrics["gpu_utilization_max_percent"].value == pytest.approx(80.0)
    assert metrics["estimated_flops_per_second"].value == pytest.approx(13333.3333333)
    assert metrics["estimated_flops_per_second"].kind is MetricKind.ESTIMATED
    assert bundle.summary["measurement_count"] == EXPECTED_MEASUREMENT_COUNT


def test_result_serializer_creates_report_payload() -> None:
    bundle = CoreMetricsEngine().compute(
        session_id="empty-session",
        configuration=Configuration(),
        runs=[],
        hardware=HardwareProfile(),
        workload=None,
        failure_message="no measurements",
    )

    payload = ResultSerializer().bundle_to_dict(bundle)

    assert payload["summary"]["status"] == "failed"
    assert payload["statistics"]["count"] == 0.0
    assert payload["metrics"][0]["name"] == "latency_mean_seconds"
