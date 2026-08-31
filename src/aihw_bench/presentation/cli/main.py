"""Typer command line interface for AI Hardware Benchmark Suite."""

from __future__ import annotations

import json
import platform
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from aihw_bench import __version__
from aihw_bench.application import (
    CORE_PLUGIN_API_VERSION,
    BenchmarkAssistant,
    BenchmarkRequest,
    BenchmarkService,
    DashboardService,
    OfficialBenchmarkSuite,
    PluginManager,
    ReportRequest,
)
from aihw_bench.domain.errors import AihwBenchError
from aihw_bench.domain.models import Configuration, Metric
from aihw_bench.infrastructure.backends import ReferenceBenchmarkBackend, default_backend_registry
from aihw_bench.infrastructure.configuration import load_configuration
from aihw_bench.infrastructure.hardware import SystemHardwareInspector
from aihw_bench.infrastructure.models import ModelLoaderRegistry
from aihw_bench.infrastructure.reporting import default_report_service
from aihw_bench.infrastructure.storage import FilesystemSessionStore
from aihw_bench.utils.serialization import write_json

app = typer.Typer(
    name="aihw-bench",
    help="Universal benchmarking and profiling for AI hardware and accelerators.",
    no_args_is_help=True,
)
console = Console()
DEFAULT_STORAGE_ROOT = Path(".aihw-bench") / "sessions"
OutputMode = Annotated[
    str,
    typer.Option(
        "--output",
        "-O",
        help="Output mode: table, json, yaml, or quiet where supported.",
    ),
]


def _installed_version(distribution: str) -> str:
    """Return an installed distribution version or a readable unavailable marker."""
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not installed"


def _print_error(exc: AihwBenchError, *, exit_code: int) -> None:
    console.print(f"[red]{exc.message}[/red]")
    console.print(f"[bold]Cause:[/bold] {exc.context.cause}")
    console.print(f"[bold]Suggestion:[/bold] {exc.context.suggestion}")
    if exc.context.documentation:
        console.print(f"[bold]Docs:[/bold] {exc.context.documentation}")
    raise typer.Exit(code=exit_code)


def _session_store(storage_root: Path) -> FilesystemSessionStore:
    return FilesystemSessionStore(storage_root)


def _load_cli_configuration(
    *,
    config_path: Path | None,
    profile: str | None,
    backend: str | None = None,
    device: str | None = None,
    batch_size: int | None = None,
    precision: str | None = None,
    warmup: int | None = None,
    iterations: int | None = None,
    output_dir: Path | None = None,
    report_formats: list[str] | None = None,
    workload_source: str | None = None,
    profiling_enabled: list[str] | None = None,
) -> Configuration:
    overrides: dict[str, object] = {}
    if backend is not None or device is not None:
        overrides["backend"] = {
            key: value
            for key, value in {"name": backend, "device": device}.items()
            if value is not None
        }
    execution = {
        key: value
        for key, value in {
            "batch_size": batch_size,
            "precision": precision,
            "warmup_iterations": warmup,
            "iterations": iterations,
        }.items()
        if value is not None
    }
    if execution:
        overrides["execution"] = execution
    if output_dir is not None or report_formats:
        overrides["reports"] = {
            key: value
            for key, value in {
                "output_dir": output_dir,
                "formats": report_formats,
            }.items()
            if value is not None
        }
    if workload_source is not None:
        overrides["workload"] = {"source": workload_source}
    if profiling_enabled:
        overrides["profiling"] = {"enabled": profiling_enabled}
    return load_configuration(config_path=config_path, profile=profile, cli_overrides=overrides)


def _benchmark_service(configuration: Configuration, storage_root: Path) -> BenchmarkService:
    store = _session_store(storage_root)
    if configuration.backend.name == "reference":
        return BenchmarkService(
            ReferenceBenchmarkBackend(),
            hardware_inspector=SystemHardwareInspector(),
            model_catalog=ModelLoaderRegistry(),
            report_service=default_report_service(),
            session_store=store,
        )
    return BenchmarkService(
        backend_registry=default_backend_registry(),
        hardware_inspector=SystemHardwareInspector(),
        model_catalog=ModelLoaderRegistry(),
        report_service=default_report_service(),
        session_store=store,
    )


def _metric_by_name(metrics: list[Metric], name: str) -> Metric | None:
    return next((metric for metric in metrics if metric.name == name), None)


@app.command("version")
def version_info() -> None:
    """Print package, Python, platform, and core dependency versions."""
    table = Table(title="AI Hardware Benchmark Suite", box=box.ASCII)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Version", style="green")

    table.add_row("aihw-bench", __version__)
    table.add_row("Python", sys.version.split()[0])
    table.add_row("Platform", platform.platform())
    table.add_row("Plugin API", CORE_PLUGIN_API_VERSION)
    table.add_row("Typer", _installed_version("typer"))
    table.add_row("Rich", _installed_version("rich"))
    table.add_row("Pydantic", _installed_version("pydantic"))

    console.print(table)


@app.command()
def doctor() -> None:
    """Run installation health checks for the current environment."""
    plugin_registry = PluginManager(configuration=Configuration()).load(activate=False)
    plugin_failures = [
        plugin for plugin in plugin_registry.plugin_metadata() if plugin.status == "failed"
    ]
    checks = [
        ("Python >= 3.12", sys.version_info >= (3, 12)),
        ("Core package import", True),
        ("Typer available", _installed_version("typer") != "not installed"),
        ("Rich available", _installed_version("rich") != "not installed"),
        ("Pydantic available", _installed_version("pydantic") != "not installed"),
        ("Plugin API available", bool(CORE_PLUGIN_API_VERSION)),
        ("Plugins valid", not plugin_failures and not plugin_registry.diagnostics),
    ]

    table = Table(title="Environment Health", box=box.ASCII)
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")

    failed = False
    for name, ok in checks:
        failed = failed or not ok
        table.add_row(name, "pass" if ok else "fail")

    console.print(table)
    for diagnostic in plugin_registry.diagnostics:
        console.print(f"[yellow]{diagnostic.message}[/yellow]")
        console.print(f"Cause: {diagnostic.cause}")

    if failed:
        raise typer.Exit(code=2)


@app.command("benchmark")
def benchmark(
    config_path: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    profile: Annotated[str | None, typer.Option("--profile")] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="Model path or workload source."),
    ] = None,
    backend: Annotated[str | None, typer.Option("--backend")] = None,
    device: Annotated[str | None, typer.Option("--device")] = None,
    batch_size: Annotated[int | None, typer.Option("--batch-size", min=1)] = None,
    precision: Annotated[str | None, typer.Option("--precision")] = None,
    warmup: Annotated[int | None, typer.Option("--warmup", min=0)] = None,
    iterations: Annotated[int | None, typer.Option("--iterations", min=1)] = None,
    storage_root: Annotated[Path, typer.Option("--storage-root")] = DEFAULT_STORAGE_ROOT,
    report_dir: Annotated[Path | None, typer.Option("--output-dir", "-o")] = None,
    report_formats: Annotated[list[str] | None, typer.Option("--report")] = None,
) -> None:
    """Run a benchmark session and persist the result."""
    try:
        configuration = _load_cli_configuration(
            config_path=config_path,
            profile=profile,
            backend=backend,
            device=device,
            batch_size=batch_size,
            precision=precision,
            warmup=warmup,
            iterations=iterations,
            output_dir=report_dir,
            report_formats=report_formats,
            workload_source=model,
        )
        session_id = f"bench-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
        service = _benchmark_service(configuration, storage_root)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Running benchmark", total=None)
            outcome = service.run(
                BenchmarkRequest(session_id=session_id, configuration=configuration)
            )
        console.print(f"[green]Benchmark completed:[/green] {outcome.session.session_id}")
        metric = outcome.result.primary_metric("latency_mean_seconds")
        if metric is not None:
            console.print(f"Mean latency: [cyan]{metric.format()}[/cyan]")
        console.print(f"Stored session: {storage_root / outcome.session.session_id}")
    except AihwBenchError as exc:
        _print_error(exc, exit_code=4)


@app.command("profile")
def profile_command(
    profiler: Annotated[list[str] | None, typer.Option("--profiler", "-p")] = None,
    config_path: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    storage_root: Annotated[Path, typer.Option("--storage-root")] = DEFAULT_STORAGE_ROOT,
    report_dir: Annotated[Path | None, typer.Option("--output-dir", "-o")] = None,
) -> None:
    """Run a benchmark with profiling configuration recorded in the session."""
    try:
        configuration = _load_cli_configuration(
            config_path=config_path,
            profile=None,
            output_dir=report_dir,
            profiling_enabled=profiler or ["process"],
        )
        session_id = f"profile-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
        outcome = _benchmark_service(configuration, storage_root).run(
            BenchmarkRequest(session_id=session_id, configuration=configuration)
        )
        console.print(f"[green]Profile session completed:[/green] {outcome.session.session_id}")
        console.print("Profilers: " + ", ".join(configuration.profiling.enabled))
    except AihwBenchError as exc:
        _print_error(exc, exit_code=4)


@app.command("report")
def generate_report(
    session_id: str,
    storage_root: Annotated[
        Path,
        typer.Option("--storage-root", help="Session storage root."),
    ] = DEFAULT_STORAGE_ROOT,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", "-o", help="Directory for generated reports."),
    ] = None,
    formats: Annotated[
        list[str] | None,
        typer.Option(
            "--format", "-f", help="Report format to generate. Repeat for multiple formats."
        ),
    ] = None,
) -> None:
    """Generate reports for a stored benchmark session."""
    try:
        store = FilesystemSessionStore(storage_root)
        session = store.load(session_id)
        artifacts = default_report_service().generate(
            ReportRequest(
                session=session,
                formats=tuple(formats) if formats else None,
                output_dir=output_dir,
            )
        )
    except AihwBenchError as exc:
        _print_error(exc, exit_code=5)

    table = Table(title="Generated Reports", box=box.ASCII)
    table.add_column("Format", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("SHA256")
    for artifact in artifacts:
        table.add_row(artifact.format, str(artifact.path), artifact.sha256 or "")
    console.print(table)


@app.command("compare")
def compare(
    baseline_session_id: str,
    candidate_session_id: str,
    metric_name: Annotated[str, typer.Option("--metric", "-m")] = "latency_mean_seconds",
    storage_root: Annotated[Path, typer.Option("--storage-root")] = DEFAULT_STORAGE_ROOT,
    output: OutputMode = "table",
) -> None:
    """Compare one metric between two stored sessions."""
    try:
        store = _session_store(storage_root)
        baseline = store.load(baseline_session_id)
        candidate = store.load(candidate_session_id)
        baseline_metric = _metric_by_name(baseline.metrics, metric_name)
        candidate_metric = _metric_by_name(candidate.metrics, metric_name)
        if baseline_metric is None or candidate_metric is None:
            raise typer.BadParameter(f"Metric {metric_name!r} must exist in both sessions.")
        assert baseline_metric is not None
        assert candidate_metric is not None
        delta = candidate_metric.compare_to(baseline_metric)
        payload = {
            "metric": metric_name,
            "baseline": baseline_metric.model_dump(mode="json"),
            "candidate": candidate_metric.model_dump(mode="json"),
            "delta": delta,
        }
        baseline_display = baseline_metric.format()
        candidate_display = candidate_metric.format()
        delta_display = f"{delta:g} {baseline_metric.unit}"
    except AihwBenchError as exc:
        _print_error(exc, exit_code=2)

    if output == "json":
        console.print(json.dumps(payload, indent=2, sort_keys=True))
        return
    table = Table(title="Session Comparison", box=box.ASCII)
    table.add_column("Metric")
    table.add_column("Baseline")
    table.add_column("Candidate")
    table.add_column("Delta")
    table.add_row(
        metric_name,
        baseline_display,
        candidate_display,
        delta_display,
    )
    console.print(table)


@app.command("export")
def export(
    session_id: str,
    storage_root: Annotated[Path, typer.Option("--storage-root")] = DEFAULT_STORAGE_ROOT,
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("exports"),
    formats: Annotated[list[str] | None, typer.Option("--format", "-f")] = None,
) -> None:
    """Export a session as JSON plus optional report formats."""
    try:
        store = _session_store(storage_root)
        session = store.load(session_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        session_json = output_dir / f"{session_id}.session.json"
        write_json(session_json, session)
        generated = [str(session_json)]
        if formats:
            artifacts = default_report_service().generate(
                ReportRequest(session=session, formats=tuple(formats), output_dir=output_dir)
            )
            generated.extend(str(artifact.path) for artifact in artifacts)
    except AihwBenchError as exc:
        _print_error(exc, exit_code=5)

    table = Table(title="Exported Artifacts", box=box.ASCII)
    table.add_column("Path", style="green")
    for path in generated:
        table.add_row(path)
    console.print(table)


@app.command("config")
def config(
    config_path: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    profile: Annotated[str | None, typer.Option("--profile")] = None,
    output: OutputMode = "yaml",
) -> None:
    """Resolve and print the effective AIHW-Bench configuration."""
    try:
        configuration = _load_cli_configuration(config_path=config_path, profile=profile)
    except AihwBenchError as exc:
        _print_error(exc, exit_code=2)

    if output == "json":
        console.print(json.dumps(configuration.model_dump(mode="json"), indent=2, sort_keys=True))
        return
    if output == "table":
        table = Table(title="Resolved Configuration", box=box.ASCII)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("profile", configuration.profile)
        table.add_row("backend", configuration.backend.name)
        table.add_row("device", configuration.backend.device)
        table.add_row("iterations", str(configuration.execution.iterations))
        table.add_row("reports", ", ".join(configuration.reports.formats))
        console.print(table)
        return
    console.print(configuration.to_resolved_yaml())


@app.command("completion")
def completion() -> None:
    """Show shell completion installation guidance."""
    console.print("Use [cyan]aihw-bench --install-completion[/cyan] to install shell completion.")


@app.command("suite")
def suite(
    action: Annotated[str, typer.Argument(help="One of: list, materialize, baselines.")],
    benchmark: Annotated[str | None, typer.Option("--benchmark", "-b")] = None,
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("benchmarks"),
) -> None:
    """Inspect or materialize the official reproducible benchmark suite."""
    official = OfficialBenchmarkSuite()
    normalized_action = action.strip().lower()
    if normalized_action == "list":
        table = Table(title="Official AIHW-Bench Suite", box=box.ASCII)
        table.add_column("ID", style="cyan")
        table.add_column("Category")
        table.add_column("Input shape")
        table.add_column("Samples")
        for definition in official.definitions():
            table.add_row(
                definition.identifier,
                definition.category,
                " x ".join(str(value) for value in definition.input_shape),
                str(definition.sample_count),
            )
        console.print(table)
        return
    if normalized_action == "materialize":
        paths = (
            (official.materialize_dataset(benchmark, output_dir),)
            if benchmark is not None
            else official.materialize_all_datasets(output_dir)
        )
        for path in paths:
            console.print(path)
        return
    if normalized_action == "baselines":
        path = official.write_baselines(output_dir / "official-baselines.json")
        console.print(path)
        return
    raise typer.BadParameter("action must be one of: list, materialize, baselines")


@app.command("dashboard")
def dashboard(
    storage_root: Annotated[Path, typer.Option("--storage-root")] = DEFAULT_STORAGE_ROOT,
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("dashboard"),
) -> None:
    """Generate a standalone interactive dashboard from stored sessions."""
    artifact = DashboardService().build(_session_store(storage_root), output_dir)
    console.print(f"[green]Dashboard generated:[/green] {artifact.path}")
    console.print(f"Sessions: {artifact.session_count}; SHA256: {artifact.sha256}")


@app.command("assistant")
def assistant(
    session_id: str,
    storage_root: Annotated[Path, typer.Option("--storage-root")] = DEFAULT_STORAGE_ROOT,
    baseline_session_id: Annotated[str | None, typer.Option("--baseline")] = None,
    output_dir: Annotated[Path | None, typer.Option("--output-dir", "-o")] = None,
) -> None:
    """Explain a benchmark and optionally compare it against a baseline session."""
    try:
        store = _session_store(storage_root)
        session = store.load(session_id)
        baseline = store.load(baseline_session_id) if baseline_session_id else None
        response = BenchmarkAssistant().explain(session, baseline)
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            path = output_dir / f"{session_id}.assistant.md"
            path.write_text(response.to_markdown(), encoding="utf-8")
            console.print(f"[green]Assistant report:[/green] {path}")
    except AihwBenchError as exc:
        _print_error(exc, exit_code=2)
        return

    console.print(f"[bold]{response.summary}[/bold]")
    for insight in response.insights:
        console.print(f"- [cyan]{insight.category}[/cyan]: {insight.summary}")
        console.print(f"  Recommendation: {insight.recommendation}")
