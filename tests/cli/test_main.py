from typing import ClassVar

from typer.testing import CliRunner

from aihw_bench.domain.models import (
    BenchmarkSession,
    Diagnostic,
    DiagnosticSeverity,
    Metric,
    MetricKind,
    SessionStatus,
)
from aihw_bench.infrastructure.storage import FilesystemSessionStore
from aihw_bench.presentation.cli import main as cli_main
from aihw_bench.presentation.cli.main import app

EXPECTED_BASELINE_LATENCY = 0.2
EXPECTED_CANDIDATE_LATENCY = 0.1
PLUGIN_FAILURE_EXIT = 2
REPORT_FAILURE_EXIT = 5
ASSISTANT_FAILURE_EXIT = 2


def _session(session_id: str, latency: float) -> BenchmarkSession:
    return BenchmarkSession(
        session_id=session_id,
        metrics=[
            Metric(
                name="latency_mean_seconds",
                display_name="Mean Latency",
                value=latency,
                unit="seconds",
                kind=MetricKind.DERIVED,
                source="metrics-engine",
            )
        ],
        backend={"name": "reference"},
    ).finalize(SessionStatus.COMPLETED)


def test_version_command_succeeds() -> None:
    result = CliRunner().invoke(app, ["version"])

    assert result.exit_code == 0
    assert "aihw-bench" in result.output
    assert "Python" in result.output


def test_doctor_command_succeeds() -> None:
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Environment Health" in result.output


def test_doctor_command_reports_plugin_diagnostics(monkeypatch) -> None:
    class FakePluginRegistry:
        diagnostics: ClassVar[list[Diagnostic]] = [
            Diagnostic(
                code="plugin.discovery_failed",
                message="Plugin demo could not be discovered.",
                severity=DiagnosticSeverity.ERROR,
                cause="broken entry point",
                suggestion="Fix plugin",
            )
        ]

        def plugin_metadata(self):
            return []

    class FakePluginManager:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def load(self, *, activate: bool = True):
            return FakePluginRegistry()

    monkeypatch.setattr(cli_main, "PluginManager", FakePluginManager)

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == PLUGIN_FAILURE_EXIT
    assert "Plugin demo could not be discovered" in result.output
    assert "broken entry point" in result.output


def test_report_command_generates_requested_formats(tmp_path) -> None:
    session = _session("cli-report-session", EXPECTED_CANDIDATE_LATENCY)
    storage_root = tmp_path / "sessions"
    output_dir = tmp_path / "reports"
    FilesystemSessionStore(storage_root).create(session)

    result = CliRunner().invoke(
        app,
        [
            "report",
            "cli-report-session",
            "--storage-root",
            str(storage_root),
            "--output-dir",
            str(output_dir),
            "--format",
            "json",
            "--format",
            "markdown",
        ],
    )

    assert result.exit_code == 0
    assert "Generated Reports" in result.output
    assert (output_dir / "cli-report-session.json").exists()
    assert (output_dir / "cli-report-session.md").exists()


def test_benchmark_command_runs_and_stores_session(tmp_path) -> None:
    storage_root = tmp_path / "sessions"
    report_dir = tmp_path / "reports"

    result = CliRunner().invoke(
        app,
        [
            "benchmark",
            "--backend",
            "reference",
            "--warmup",
            "0",
            "--iterations",
            "1",
            "--storage-root",
            str(storage_root),
            "--output-dir",
            str(report_dir),
            "--report",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert "Benchmark completed" in result.output
    assert len(FilesystemSessionStore(storage_root).list_sessions()) == 1
    assert len(list(report_dir.glob("*.json"))) == 1


def test_profile_command_runs_with_profiler_configuration(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "profile",
            "--profiler",
            "process",
            "--storage-root",
            str(tmp_path / "sessions"),
            "--output-dir",
            str(tmp_path / "reports"),
        ],
    )

    assert result.exit_code == 0
    assert "Profile session completed" in result.output
    assert "process" in result.output


def test_compare_command_outputs_metric_delta(tmp_path) -> None:
    storage_root = tmp_path / "sessions"
    store = FilesystemSessionStore(storage_root)
    store.create(_session("baseline", EXPECTED_BASELINE_LATENCY))
    store.create(_session("candidate", EXPECTED_CANDIDATE_LATENCY))

    result = CliRunner().invoke(
        app,
        [
            "compare",
            "baseline",
            "candidate",
            "--storage-root",
            str(storage_root),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert '"delta": -0.1' in result.output


def test_compare_command_outputs_table(tmp_path) -> None:
    storage_root = tmp_path / "sessions"
    store = FilesystemSessionStore(storage_root)
    store.create(_session("baseline", EXPECTED_BASELINE_LATENCY))
    store.create(_session("candidate", EXPECTED_CANDIDATE_LATENCY))

    result = CliRunner().invoke(
        app,
        [
            "compare",
            "baseline",
            "candidate",
            "--storage-root",
            str(storage_root),
        ],
    )

    assert result.exit_code == 0
    assert "Session Comparison" in result.output


def test_compare_command_rejects_missing_metric(tmp_path) -> None:
    storage_root = tmp_path / "sessions"
    store = FilesystemSessionStore(storage_root)
    store.create(_session("baseline", EXPECTED_BASELINE_LATENCY))
    store.create(_session("candidate", EXPECTED_CANDIDATE_LATENCY))

    result = CliRunner().invoke(
        app,
        [
            "compare",
            "baseline",
            "candidate",
            "--storage-root",
            str(storage_root),
            "--metric",
            "missing_metric",
        ],
    )

    assert result.exit_code != 0
    assert "missing_metric" in result.output


def test_export_command_writes_session_and_reports(tmp_path) -> None:
    storage_root = tmp_path / "sessions"
    output_dir = tmp_path / "exports"
    FilesystemSessionStore(storage_root).create(
        _session("export-session", EXPECTED_CANDIDATE_LATENCY)
    )

    result = CliRunner().invoke(
        app,
        [
            "export",
            "export-session",
            "--storage-root",
            str(storage_root),
            "--output-dir",
            str(output_dir),
            "--format",
            "csv",
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "export-session.session.json").exists()
    assert (output_dir / "export-session.csv").exists()


def test_export_command_writes_session_without_report_formats(tmp_path) -> None:
    storage_root = tmp_path / "sessions"
    output_dir = tmp_path / "exports"
    FilesystemSessionStore(storage_root).create(
        _session("export-session", EXPECTED_CANDIDATE_LATENCY)
    )

    result = CliRunner().invoke(
        app,
        [
            "export",
            "export-session",
            "--storage-root",
            str(storage_root),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "export-session.session.json").exists()


def test_report_command_returns_error_for_missing_session(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "report",
            "missing",
            "--storage-root",
            str(tmp_path / "sessions"),
        ],
    )

    assert result.exit_code == REPORT_FAILURE_EXIT
    assert "Session does not exist" in result.output


def test_config_command_outputs_json() -> None:
    result = CliRunner().invoke(app, ["config", "--output", "json"])

    assert result.exit_code == 0
    assert '"schema_version"' in result.output
    assert '"backend"' in result.output


def test_config_command_outputs_table() -> None:
    result = CliRunner().invoke(app, ["config", "--output", "table"])

    assert result.exit_code == 0
    assert "Resolved Configuration" in result.output


def test_config_command_outputs_yaml() -> None:
    result = CliRunner().invoke(app, ["config"])

    assert result.exit_code == 0
    assert "schema_version:" in result.output


def test_completion_command_describes_installation() -> None:
    result = CliRunner().invoke(app, ["completion"])

    assert result.exit_code == 0
    assert "--install-completion" in result.output


def test_help_lists_core_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ["benchmark", "compare", "config", "doctor", "export", "profile", "report"]:
        assert command in result.output


def test_suite_command_lists_official_contracts() -> None:
    result = CliRunner().invoke(app, ["suite", "list"])

    assert result.exit_code == 0
    assert "Official AIHW-Bench Suite" in result.output
    assert "image-classification" in result.output


def test_suite_command_materializes_one_contract(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        ["suite", "materialize", "--benchmark", "tinyml", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert (tmp_path / "tinyml.dataset.json").exists()


def test_suite_command_writes_reference_baselines(tmp_path) -> None:
    result = CliRunner().invoke(app, ["suite", "baselines", "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / "official-baselines.json").exists()


def test_suite_command_rejects_unknown_action() -> None:
    result = CliRunner().invoke(app, ["suite", "unknown"])

    assert result.exit_code != 0
    assert "action must be one of" in result.output


def test_dashboard_command_generates_static_assets(tmp_path) -> None:
    storage_root = tmp_path / "sessions"
    FilesystemSessionStore(storage_root).create(_session("dashboard-session", 0.1))

    result = CliRunner().invoke(
        app,
        [
            "dashboard",
            "--storage-root",
            str(storage_root),
            "--output-dir",
            str(tmp_path / "dashboard"),
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "dashboard" / "index.html").exists()
    assert (tmp_path / "dashboard" / "assets" / "dashboard.js").exists()


def test_assistant_command_writes_grounded_report(tmp_path) -> None:
    storage_root = tmp_path / "sessions"
    FilesystemSessionStore(storage_root).create(_session("assistant-session", 0.1))

    result = CliRunner().invoke(
        app,
        [
            "assistant",
            "assistant-session",
            "--storage-root",
            str(storage_root),
            "--output-dir",
            str(tmp_path / "assistant-reports"),
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "assistant-reports" / "assistant-session.assistant.md").exists()


def test_assistant_command_reports_missing_session(tmp_path) -> None:
    result = CliRunner().invoke(
        app, ["assistant", "missing", "--storage-root", str(tmp_path / "sessions")]
    )

    assert result.exit_code == ASSISTANT_FAILURE_EXIT
    assert "Session does not exist" in result.output
