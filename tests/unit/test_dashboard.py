from __future__ import annotations

from aihw_bench.application import DashboardService
from aihw_bench.domain.models import BenchmarkSession, Metric, MetricKind, SessionStatus
from aihw_bench.infrastructure.storage import FilesystemSessionStore

EXPECTED_BOUNDED_SESSIONS = 2


def test_dashboard_renders_interactive_session_browser(tmp_path) -> None:
    store = FilesystemSessionStore(tmp_path / "sessions")
    session = BenchmarkSession(
        session_id="dashboard-session",
        metrics=[
            Metric(
                name="latency_mean_seconds",
                display_name="Latency",
                value=0.1,
                unit="seconds",
                kind=MetricKind.DERIVED,
                source="test",
            )
        ],
        backend={"name": "reference"},
    ).finalize(SessionStatus.COMPLETED)
    store.create(session)

    artifact = DashboardService().build(store, tmp_path / "dashboard")
    html = artifact.path.read_text(encoding="utf-8")

    assert artifact.session_count == 1
    assert artifact.sha256
    assert "Benchmark history" in html
    assert "Toggle theme" in html
    assert "Export CSV" in html
    assert "dashboard-session" in html


def test_dashboard_renders_persisted_malicious_values_only_as_json_data(tmp_path) -> None:
    store = FilesystemSessionStore(tmp_path / "sessions")
    payload = '<script>alert(1)</script><img src=x onerror=alert(1)>"><script>alert(1)</script>'
    session = BenchmarkSession(
        session_id="malicious-session",
        backend={"name": payload},
        metrics=[
            Metric(
                name="latency_mean_seconds",
                display_name=payload,
                value=0.1,
                unit="seconds",
                kind=MetricKind.DERIVED,
                source=payload,
            )
        ],
    ).finalize(SessionStatus.COMPLETED)
    store.create(session)

    artifact = DashboardService().build(store, tmp_path / "dashboard", title=payload)
    html = artifact.path.read_text(encoding="utf-8")
    script = (tmp_path / "dashboard" / "assets" / "dashboard.js").read_text(encoding="utf-8")

    assert "Content-Security-Policy" in html
    assert "<\\/script>" in html
    assert "innerHTML" not in script
    assert "insertAdjacentHTML" not in script
    assert "textContent" in script
    assert "javascript:" not in html.lower()


def test_dashboard_bounds_initial_history_payload(tmp_path) -> None:
    store = FilesystemSessionStore(tmp_path / "sessions")
    for index in range(3):
        store.create(
            BenchmarkSession(session_id=f"session-{index}").finalize(SessionStatus.COMPLETED)
        )

    artifact = DashboardService(max_sessions=EXPECTED_BOUNDED_SESSIONS).build(
        store, tmp_path / "dashboard"
    )
    html = artifact.path.read_text(encoding="utf-8")

    assert artifact.session_count == EXPECTED_BOUNDED_SESSIONS
    assert "session-0" not in html
    assert "session-1" in html
    assert "session-2" in html
