"""Pydantic data models for persisted AIHW-Bench records."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aihw_bench.domain.errors import MetricError, SessionError

SCHEMA_VERSION = "1.0"


class FrozenModel(BaseModel):
    """Base class for immutable domain models."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_assignment=True)


class SessionStatus(StrEnum):
    """Lifecycle states persisted for benchmark sessions."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class ExecutionPhase(StrEnum):
    """Execution phases recorded in session data."""

    WARMUP = "warmup"
    MEASUREMENT = "measurement"
    CALIBRATION = "calibration"
    CLEANUP = "cleanup"


class ExecutionStatus(StrEnum):
    """Execution result status."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class MetricKind(StrEnum):
    """Metric provenance category."""

    MEASURED = "measured"
    DERIVED = "derived"
    ESTIMATED = "estimated"
    METADATA = "metadata"
    UNAVAILABLE = "unavailable"


class DiagnosticSeverity(StrEnum):
    """Severity for user-facing diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ConfigurationSource(FrozenModel):
    """Records one source that contributed to a resolved configuration."""

    name: str
    kind: Literal["default", "file", "environment", "cli", "profile"]
    path: str | None = None


class WorkloadConfig(FrozenModel):
    """Configuration for the workload under test."""

    source: str | None = None
    name: str | None = None
    input_shapes: dict[str, list[int]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BackendConfig(FrozenModel):
    """Configuration for backend selection and backend-specific options."""

    name: str = "reference"
    device: str = "cpu"
    options: dict[str, Any] = Field(default_factory=dict)


class ExecutionConfig(FrozenModel):
    """Configuration for benchmark execution policy."""

    warmup_iterations: int = Field(default=1, ge=0)
    iterations: int = Field(default=5, ge=1)
    timeout_seconds: float | None = Field(default=60.0, gt=0)
    retry_attempts: int = Field(default=0, ge=0)
    batch_size: int = Field(default=1, ge=1)
    precision: str = "fp32"


class ProfilingConfig(FrozenModel):
    """Configuration for profiler selection."""

    enabled: list[str] = Field(default_factory=list)
    sampling_interval_seconds: float = Field(default=0.1, gt=0)


class MetricsConfig(FrozenModel):
    """Configuration for metric selection and thresholds."""

    enabled: list[str] = Field(default_factory=lambda: ["latency", "throughput"])
    thresholds: dict[str, float] = Field(default_factory=dict)


class ReportsConfig(FrozenModel):
    """Configuration for report generation."""

    formats: list[str] = Field(default_factory=lambda: ["json", "markdown"])
    output_dir: Path = Path("reports")


class StorageConfig(FrozenModel):
    """Configuration for session storage."""

    root: Path = Path(".aihw-bench") / "sessions"


class PluginsConfig(FrozenModel):
    """Configuration for plugin loading policy."""

    enabled: list[str] = Field(default_factory=list)
    disabled: list[str] = Field(default_factory=list)
    strict: bool = False


class Configuration(FrozenModel):
    """Resolved AIHW-Bench configuration.

    The model is immutable and records the sources used to build it.
    """

    schema_version: str = SCHEMA_VERSION
    sources: list[ConfigurationSource] = Field(default_factory=list)
    profile: str = "default"
    workload: WorkloadConfig = Field(default_factory=WorkloadConfig)
    backend: BackendConfig = Field(default_factory=BackendConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    profiling: ProfilingConfig = Field(default_factory=ProfilingConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)
    tags: dict[str, str] = Field(default_factory=dict)

    def explain_sources(self) -> list[str]:
        """Return readable source descriptions in precedence order."""
        return [
            f"{source.kind}:{source.name}" + (f" ({source.path})" if source.path else "")
            for source in self.sources
        ]

    def to_resolved_yaml(self) -> str:
        """Serialize the resolved configuration as YAML."""
        import yaml

        return yaml.safe_dump(self.model_dump(mode="json"), sort_keys=True)


class Diagnostic(FrozenModel):
    """User-facing diagnostic with cause and suggested fix."""

    code: str
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.INFO
    cause: str
    suggestion: str
    documentation: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Metric(FrozenModel):
    """Measured, derived, estimated, or metadata metric."""

    name: str
    display_name: str
    value: float | int | str | None
    unit: str
    kind: MetricKind
    source: str
    higher_is_better: bool | None = None
    assumptions: list[str] = Field(default_factory=list)
    precision: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)

    def format(self) -> str:
        """Format a metric for human-readable output."""
        return f"{self.value} {self.unit}" if self.value is not None else f"unavailable {self.unit}"

    def compare_to(self, other: Metric) -> float:
        """Return numeric delta from another compatible metric."""
        if self.name != other.name or self.unit != other.unit:
            raise MetricError(
                "Metrics are not comparable.",
                cause=f"{self.name}/{self.unit} cannot be compared with {other.name}/{other.unit}.",
                suggestion="Compare metrics with the same name and unit.",
                documentation="docs/engineering/data-model.md",
            )
        if not isinstance(self.value, int | float) or not isinstance(other.value, int | float):
            raise MetricError(
                "Metric values are not numeric.",
                cause="At least one metric value is non-numeric or unavailable.",
                suggestion="Only numeric metrics can be compared.",
                documentation="docs/engineering/data-model.md",
            )
        return float(self.value) - float(other.value)


class HardwareProfile(FrozenModel):
    """Host and target hardware metadata captured for a session."""

    host_name: str | None = None
    cpu: dict[str, Any] = Field(default_factory=dict)
    memory: dict[str, Any] = Field(default_factory=dict)
    gpu: dict[str, Any] = Field(default_factory=dict)
    accelerators: list[dict[str, Any]] = Field(default_factory=list)
    embedded_target: dict[str, Any] = Field(default_factory=dict)
    simulator: dict[str, Any] = Field(default_factory=dict)
    driver_versions: dict[str, str] = Field(default_factory=dict)
    firmware_versions: dict[str, str] = Field(default_factory=dict)
    thermal_policy: str | None = None
    power_policy: str | None = None

    def summary(self) -> dict[str, Any]:
        """Return a compact hardware summary."""
        return {
            "host_name": self.host_name,
            "cpu": self.cpu.get("name"),
            "gpu": self.gpu.get("name"),
            "accelerators": len(self.accelerators),
        }

    def capability_report(self) -> dict[str, Any]:
        """Return normalized capabilities for backend selection and reports."""
        gpu_devices = self.gpu.get("devices", [])
        return {
            "cpu": {
                "vendor": self.cpu.get("vendor", "unknown"),
                "architecture": self.cpu.get("architecture"),
                "features": list(self.cpu.get("features", [])),
                "apple_silicon": bool(self.cpu.get("apple_silicon")),
            },
            "gpu": {
                "available": bool(self.gpu.get("available")),
                "backend": self.gpu.get("backend"),
                "device_count": len(gpu_devices) if isinstance(gpu_devices, list) else 0,
                "vendors": sorted(
                    {
                        str(device.get("vendor", "unknown"))
                        for device in gpu_devices
                        if isinstance(device, dict)
                    }
                ),
                "capabilities": sorted(
                    {
                        str(capability)
                        for device in gpu_devices
                        if isinstance(device, dict)
                        for capability in device.get("capabilities", [])
                    }
                ),
            },
            "embedded": dict(self.embedded_target),
            "accelerators": [dict(accelerator) for accelerator in self.accelerators],
            "simulator": dict(self.simulator),
        }


class ModelMetadata(FrozenModel):
    """Metadata for a benchmark workload or model."""

    model_id: str
    name: str
    format: str
    framework: str | None = None
    source: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    input_shapes: dict[str, list[int]] = Field(default_factory=dict)
    output_shapes: dict[str, list[int]] = Field(default_factory=dict)
    input_tensors: list[dict[str, Any]] = Field(default_factory=list)
    output_tensors: list[dict[str, Any]] = Field(default_factory=list)
    precision: str | None = None
    supported_precision: list[str] = Field(default_factory=list)
    supported_batch_sizes: list[int] = Field(default_factory=list)
    parameters: int | None = Field(default=None, ge=0)
    macs: int | None = Field(default=None, ge=0)
    flops_estimate: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        """Return a stable fingerprint for comparison and caching."""
        import hashlib
        import json

        payload = self.model_dump(mode="json")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable model description."""
        return self.model_dump(mode="json")

    def summary(self) -> dict[str, Any]:
        """Return summary fields suitable for reports."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "format": self.format,
            "precision": self.precision,
        }


class ExecutionResult(FrozenModel):
    """One backend execution event."""

    execution_id: str
    phase: ExecutionPhase
    iteration: int = Field(ge=0)
    started_at: datetime
    ended_at: datetime
    duration_seconds: float = Field(ge=0)
    status: ExecutionStatus
    observations: dict[str, Any] = Field(default_factory=dict)
    backend_metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    @field_validator("started_at", "ended_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Require timezone-aware timestamps."""
        if value.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_time_order(self) -> ExecutionResult:
        """Ensure execution end time is not before start time."""
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must be greater than or equal to started_at")
        return self


class Profile(FrozenModel):
    """Profiler samples and summaries."""

    profile_id: str
    profiler_name: str
    scope: str
    sampling_interval_seconds: float = Field(gt=0)
    samples: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    diagnostics: list[Diagnostic] = Field(default_factory=list)


class BenchmarkResult(FrozenModel):
    """Aggregate result for a workload/backend/device combination."""

    result_id: str
    session_id: str
    status: ExecutionStatus
    primary_metrics: list[Metric] = Field(default_factory=list)
    secondary_metrics: list[Metric] = Field(default_factory=list)
    statistics: dict[str, float] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    comparison_keys: dict[str, str] = Field(default_factory=dict)
    error: str | None = None

    def is_successful(self) -> bool:
        """Return whether the benchmark result completed successfully."""
        return self.status is ExecutionStatus.SUCCESS

    def primary_metric(self, name: str) -> Metric | None:
        """Return a primary metric by name."""
        return next((metric for metric in self.primary_metrics if metric.name == name), None)


class RunHistory(FrozenModel):
    """Historical comparison metadata."""

    history_id: str
    session_ids: list[str]
    comparison_keys: dict[str, str] = Field(default_factory=dict)
    baseline_session_id: str
    candidate_session_id: str
    deltas: dict[str, float] = Field(default_factory=dict)
    thresholds: dict[str, float] = Field(default_factory=dict)
    outcomes: dict[str, str] = Field(default_factory=dict)


class PluginMetadata(FrozenModel):
    """Validated plugin descriptor metadata."""

    name: str
    version: str
    api_version: str
    package: str
    description: str
    providers: list[str]
    dependencies: list[str] = Field(default_factory=list)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    status: str = "available"
    diagnostics: list[Diagnostic] = Field(default_factory=list)

    def is_compatible(self, core_api_version: str) -> bool:
        """Return whether the plugin API version matches the core API version."""
        return self.api_version == core_api_version

    def provider_names(self) -> list[str]:
        """Return provider names declared by this plugin."""
        return list(self.providers)


class ExportArtifact(FrozenModel):
    """Generated artifact metadata and integrity information."""

    artifact_id: str
    kind: str
    format: str
    path: Path
    sha256: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_session_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at")
    @classmethod
    def require_created_at_timezone(cls, value: datetime) -> datetime:
        """Require timezone-aware artifact timestamps."""
        if value.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        return value


class BenchmarkSession(FrozenModel):
    """Immutable top-level benchmark session record."""

    session_id: str
    schema_version: str = SCHEMA_VERSION
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    status: SessionStatus = SessionStatus.CREATED
    configuration: Configuration = Field(default_factory=Configuration)
    hardware: HardwareProfile = Field(default_factory=HardwareProfile)
    system: dict[str, Any] = Field(default_factory=dict)
    workload: ModelMetadata | None = None
    backend: dict[str, Any] = Field(default_factory=dict)
    runs: list[ExecutionResult] = Field(default_factory=list)
    results: list[BenchmarkResult] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    profiles: list[Profile] = Field(default_factory=list)
    artifacts: list[ExportArtifact] = Field(default_factory=list)
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    plugins: list[PluginMetadata] = Field(default_factory=list)

    @field_validator("created_at", "completed_at")
    @classmethod
    def require_session_timezone(cls, value: datetime | None) -> datetime | None:
        """Require timezone-aware session timestamps."""
        if value is not None and value.tzinfo is None:
            raise ValueError("session timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_completion_time(self) -> BenchmarkSession:
        """Ensure completed sessions include completion time."""
        finished_states = {
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
            SessionStatus.PARTIAL,
        }
        if self.status in finished_states and self.completed_at is None:
            raise ValueError("finished sessions must include completed_at")
        return self

    def finalize(
        self,
        status: SessionStatus,
        *,
        completed_at: datetime | None = None,
    ) -> BenchmarkSession:
        """Return a finalized copy of the session."""
        if self.completed_at is not None:
            raise SessionError(
                "Session is already finalized.",
                cause=f"Session {self.session_id} has completed_at set.",
                suggestion="Load the finalized session as read-only or create a new session.",
                documentation="docs/engineering/storage-design.md",
            )
        if status is SessionStatus.CREATED or status is SessionStatus.RUNNING:
            raise SessionError(
                "Final status is invalid.",
                cause=f"{status.value} is not a terminal session status.",
                suggestion="Finalize sessions with completed, failed, cancelled, or partial.",
                documentation="docs/engineering/data-model.md",
            )
        return self.model_copy(
            update={"status": status, "completed_at": completed_at or datetime.now(UTC)}
        )

    def add_artifact(self, artifact: ExportArtifact) -> BenchmarkSession:
        """Return a copy of the session with a new artifact."""
        if self.completed_at is not None:
            raise SessionError(
                "Cannot add artifacts to a finalized session.",
                cause=f"Session {self.session_id} is immutable.",
                suggestion="Create derived artifacts in a new output location.",
                documentation="docs/engineering/storage-design.md",
            )
        return self.model_copy(update={"artifacts": [*self.artifacts, artifact]})
