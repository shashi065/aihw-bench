from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aihw_bench.application import BenchmarkAssistant
from aihw_bench.domain.models import (
    BenchmarkSession,
    ExecutionConfig,
    ExecutionPhase,
    ExecutionResult,
    ExecutionStatus,
    Metric,
    MetricKind,
    SessionStatus,
)


def _session(session_id: str, latency: float, warmup: int = 0) -> BenchmarkSession:
    started = datetime(2026, 1, 1, tzinfo=UTC)
    runs = [
        ExecutionResult(
            execution_id="run",
            phase=ExecutionPhase.MEASUREMENT,
            iteration=0,
            started_at=started,
            ended_at=started + timedelta(seconds=latency),
            duration_seconds=latency,
            status=ExecutionStatus.SUCCESS,
        )
    ]
    session = BenchmarkSession(
        session_id=session_id,
        runs=runs,
        metrics=[
            Metric(
                name="latency_mean_seconds",
                display_name="Latency",
                value=latency,
                unit="seconds",
                kind=MetricKind.DERIVED,
                source="test",
            )
        ],
    ).finalize(SessionStatus.COMPLETED)
    return session.model_copy(
        update={
            "configuration": session.configuration.model_copy(
                update={"execution": ExecutionConfig(warmup_iterations=warmup)}
            )
        }
    )


def test_assistant_explains_and_recommends_warmup() -> None:
    response = BenchmarkAssistant().explain(_session("candidate", 0.2))
    assert "candidate" in response.summary
    assert any(insight.category == "optimization" for insight in response.insights)
    assert response.recommended_configuration.execution.warmup_iterations == 1


def test_assistant_detects_comparison_regression_and_generates_report() -> None:
    response = BenchmarkAssistant().explain(
        _session("candidate", 0.2), _session("baseline", 0.1, 1)
    )
    assert any(insight.category == "hardware comparison" for insight in response.insights)
    assert "AIHW-Bench Assistant Report" in response.to_markdown()
