from datetime import UTC, datetime, timedelta

import pytest

from aihw_bench.domain.errors import MetricError, SessionError
from aihw_bench.domain.models import (
    BenchmarkSession,
    ExecutionPhase,
    ExecutionResult,
    ExecutionStatus,
    Metric,
    MetricKind,
    ModelMetadata,
    SessionStatus,
)

EXPECTED_LATENCY_DELTA = -2.5


def test_metric_comparison_requires_matching_name_and_unit() -> None:
    latency = Metric(
        name="latency",
        display_name="Latency",
        value=10.0,
        unit="ms",
        kind=MetricKind.MEASURED,
        source="test",
    )
    throughput = Metric(
        name="throughput",
        display_name="Throughput",
        value=20.0,
        unit="samples/s",
        kind=MetricKind.MEASURED,
        source="test",
    )

    with pytest.raises(MetricError):
        latency.compare_to(throughput)


def test_metric_comparison_returns_numeric_delta() -> None:
    baseline = Metric(
        name="latency",
        display_name="Latency",
        value=12.5,
        unit="ms",
        kind=MetricKind.MEASURED,
        source="test",
    )
    candidate = baseline.model_copy(update={"value": 10.0})

    assert candidate.compare_to(baseline) == EXPECTED_LATENCY_DELTA


def test_execution_result_requires_timezone_aware_timestamps() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ExecutionResult(
            execution_id="run-1",
            phase=ExecutionPhase.MEASUREMENT,
            iteration=0,
            started_at=datetime(2026, 1, 1),
            ended_at=datetime(2026, 1, 1),
            duration_seconds=0.0,
            status=ExecutionStatus.SUCCESS,
        )


def test_benchmark_session_finalize_returns_immutable_copy() -> None:
    session = BenchmarkSession(session_id="session-1")

    finalized = session.finalize(SessionStatus.COMPLETED)

    assert session.status is SessionStatus.CREATED
    assert finalized.status is SessionStatus.COMPLETED
    assert finalized.completed_at is not None

    with pytest.raises(SessionError):
        finalized.finalize(SessionStatus.FAILED)


def test_finished_session_requires_completed_at() -> None:
    with pytest.raises(ValueError, match="finished sessions"):
        BenchmarkSession(session_id="session-1", status=SessionStatus.COMPLETED)


def test_model_metadata_summary_is_stable() -> None:
    metadata = ModelMetadata(
        model_id="resnet-test",
        name="ResNet Test",
        format="onnx",
        precision="fp32",
    )

    assert metadata.summary() == {
        "model_id": "resnet-test",
        "name": "ResNet Test",
        "format": "onnx",
        "precision": "fp32",
    }


def test_execution_result_rejects_end_before_start() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="ended_at"):
        ExecutionResult(
            execution_id="run-1",
            phase=ExecutionPhase.MEASUREMENT,
            iteration=0,
            started_at=now,
            ended_at=now - timedelta(seconds=1),
            duration_seconds=0.0,
            status=ExecutionStatus.SUCCESS,
        )
