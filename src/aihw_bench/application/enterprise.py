"""Enterprise workspace, marketplace, remote-execution, and scheduling foundations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import yaml

from aihw_bench.domain.errors import ConfigurationError
from aihw_bench.domain.models import BenchmarkSession, Configuration, Metric

ENTERPRISE_DOCUMENTATION = "docs/enterprise.md"


@dataclass(frozen=True, slots=True)
class WorkspaceProfile:
    """Named workspace defaults applied before project configuration."""

    name: str
    configuration: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ProjectConfiguration:
    """Project-scoped configuration and selected workspace profile."""

    name: str
    profile: str
    configuration: dict[str, Any]


class WorkspaceManager:
    """Persist workspace profiles and project configurations as readable YAML."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.profiles_dir = root / "profiles"
        self.projects_dir = root / "projects"

    def save_profile(self, profile: WorkspaceProfile) -> Path:
        return self._write(self.profiles_dir / f"{profile.name}.yaml", asdict(profile))

    def load_profile(self, name: str) -> WorkspaceProfile:
        return WorkspaceProfile(**self._read(self.profiles_dir / f"{name}.yaml"))

    def save_project(self, project: ProjectConfiguration) -> Path:
        return self._write(self.projects_dir / f"{project.name}.yaml", asdict(project))

    def load_project(self, name: str) -> ProjectConfiguration:
        return ProjectConfiguration(**self._read(self.projects_dir / f"{name}.yaml"))

    def resolve(self, project_name: str) -> Configuration:
        """Resolve profile defaults with project configuration taking precedence."""
        project = self.load_project(project_name)
        profile = self.load_profile(project.profile)
        merged = {**profile.configuration, **project.configuration}
        try:
            return Configuration.model_validate(merged)
        except Exception as exc:
            raise ConfigurationError(
                "Workspace project configuration is invalid.",
                cause=str(exc),
                suggestion="Fix the project or workspace profile YAML.",
                documentation=ENTERPRISE_DOCUMENTATION,
            ) from exc

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
        return path

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ConfigurationError(
                "Workspace configuration does not exist.",
                cause=str(exc),
                suggestion="Create the workspace profile or project before loading it.",
                documentation=ENTERPRISE_DOCUMENTATION,
            ) from exc
        if not isinstance(payload, dict):
            raise ConfigurationError(
                "Workspace configuration must be a mapping.",
                cause=f"{path} did not contain a mapping.",
                suggestion="Use YAML key-value mappings for workspace configuration.",
                documentation=ENTERPRISE_DOCUMENTATION,
            )
        return payload


@dataclass(frozen=True, slots=True)
class MarketplacePlugin:
    """Marketplace listing metadata; installation remains an explicit user action."""

    name: str
    version: str
    package: str
    description: str
    api_version: str
    providers: tuple[str, ...]
    repository: str | None = None


class PluginMarketplace:
    """Read and write a versioned local marketplace index."""

    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path

    def publish(self, plugin: MarketplacePlugin) -> None:
        entries = {entry.name: entry for entry in self.list()}
        entries[plugin.name] = plugin
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            json.dumps(
                {"schema_version": "1.0", "plugins": [asdict(item) for item in entries.values()]},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def list(self, query: str | None = None) -> tuple[MarketplacePlugin, ...]:
        if not self.index_path.exists():
            return ()
        raw = json.loads(self.index_path.read_text(encoding="utf-8"))
        entries = tuple(
            MarketplacePlugin(**{**item, "providers": tuple(item["providers"])})
            for item in raw.get("plugins", [])
        )
        if not query:
            return tuple(sorted(entries, key=lambda entry: entry.name))
        normalized = query.lower()
        return tuple(entry for entry in entries if normalized in json.dumps(asdict(entry)).lower())


@dataclass(frozen=True, slots=True)
class RemoteBenchmarkRequest:
    """Transport-neutral remote benchmark request; caller supplies transport security."""

    request_id: str
    agent: str
    configuration: dict[str, Any]
    submitted_at: datetime

    def to_payload(self) -> dict[str, Any]:
        return {**asdict(self), "submitted_at": self.submitted_at.isoformat()}


class RemoteBenchmarkAgent(Protocol):
    """Remote-agent contract for authenticated transport adapters."""

    def submit(self, request: RemoteBenchmarkRequest) -> str: ...


@dataclass(frozen=True, slots=True)
class BenchmarkSchedule:
    """Pollable interval schedule; execution is owned by a dedicated runner."""

    name: str
    project: str
    interval_minutes: int
    enabled: bool = True
    last_run_at: datetime | None = None

    def due_at(self) -> datetime:
        return (
            self.last_run_at + timedelta(minutes=self.interval_minutes)
            if self.last_run_at
            else datetime.now(UTC)
        )

    def is_due(self, now: datetime | None = None) -> bool:
        if not self.enabled:
            return False
        return self.last_run_at is None or (now or datetime.now(UTC)) >= self.due_at()


class ResultComparator:
    """Compare matching numeric metrics from two persisted sessions."""

    def compare(self, baseline: BenchmarkSession, candidate: BenchmarkSession) -> dict[str, float]:
        baseline_metrics = self._numeric_metrics(baseline.metrics)
        candidate_metrics = self._numeric_metrics(candidate.metrics)
        return {
            name: candidate_metrics[name] - value
            for name, value in baseline_metrics.items()
            if name in candidate_metrics
        }

    @staticmethod
    def _numeric_metrics(metrics: list[Metric]) -> dict[str, float]:
        return {
            metric.name: float(metric.value)
            for metric in metrics
            if isinstance(metric.value, int | float)
        }


class ArtifactCatalog(Protocol):
    """Minimal artifact management port compatible with session stores."""

    def store_artifact(self, session_id: str, source: Path, *, kind: str, format: str) -> Any: ...
