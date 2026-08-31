from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from aihw_bench.application import (
    BenchmarkSchedule,
    MarketplacePlugin,
    PluginMarketplace,
    ProjectConfiguration,
    ResultComparator,
    WorkspaceManager,
    WorkspaceProfile,
)
from aihw_bench.domain.errors import ConfigurationError
from aihw_bench.domain.models import BenchmarkSession, Metric, MetricKind, SessionStatus
from aihw_bench.infrastructure.storage import SqliteHistoryStore

EXPECTED_PROJECT_ITERATIONS = 9
EXPECTED_LATENCY_DELTA = 0.1


def _session(session_id: str, latency: float) -> BenchmarkSession:
    return BenchmarkSession(
        session_id=session_id,
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
        backend={"name": "reference"},
    ).finalize(SessionStatus.COMPLETED)


def test_workspace_resolves_project_over_profile(tmp_path) -> None:
    workspace = WorkspaceManager(tmp_path)
    workspace.save_profile(
        WorkspaceProfile("shared", {"backend": {"name": "reference", "device": "cpu"}})
    )
    workspace.save_project(
        ProjectConfiguration("vision", "shared", {"execution": {"iterations": 9}})
    )
    assert workspace.resolve("vision").execution.iterations == EXPECTED_PROJECT_ITERATIONS


def test_marketplace_publishes_and_searches(tmp_path) -> None:
    marketplace = PluginMarketplace(tmp_path / "marketplace.json")
    marketplace.publish(
        MarketplacePlugin("remote-agent", "1", "agent", "Remote execution", "1.0", ("hardware",))
    )
    assert marketplace.list("remote")[0].name == "remote-agent"


def test_sqlite_history_filters_sessions(tmp_path) -> None:
    history = SqliteHistoryStore(tmp_path / "history.db")
    history.index(_session("one", 0.1))
    assert history.query(backend="reference")[0].session_id == "one"


def test_result_comparator_returns_shared_metric_delta() -> None:
    assert (
        ResultComparator().compare(_session("base", 0.1), _session("next", 0.2))[
            "latency_mean_seconds"
        ]
        == EXPECTED_LATENCY_DELTA
    )


def test_new_schedule_is_due_and_completed_schedule_waits() -> None:
    schedule = BenchmarkSchedule("nightly", "vision", 60)
    assert schedule.is_due()
    completed = BenchmarkSchedule("nightly", "vision", 60, last_run_at=datetime.now(UTC))
    assert not completed.is_due()
    assert completed.is_due(datetime.now(UTC) + timedelta(minutes=61))


def test_sqlite_history_query_filters_and_rejects_invalid_limit(tmp_path) -> None:
    history = SqliteHistoryStore(tmp_path / "history.db")
    history.index(_session("cpu", 0.1))
    other = _session("other", 0.2).model_copy(update={"backend": {"name": "gpu"}})
    history.index(other)

    assert [record.session_id for record in history.query(backend="gpu")] == ["other"]
    with pytest.raises(ValueError, match="positive"):
        history.query(limit=0)


def test_workspace_rejects_non_mapping_configuration(tmp_path) -> None:
    workspace = WorkspaceManager(tmp_path)
    workspace.profiles_dir.mkdir(parents=True)
    (workspace.profiles_dir / "invalid.yaml").write_text("- not-a-mapping\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="must be a mapping"):
        workspace.load_profile("invalid")
