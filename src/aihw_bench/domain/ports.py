"""Domain port protocols for benchmark execution."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from aihw_bench.domain.models import (
    Configuration,
    ExecutionPhase,
    ExecutionResult,
    HardwareProfile,
    Metric,
    ModelMetadata,
)


@runtime_checkable
class BenchmarkBackend(Protocol):
    """Contract for a backend that can prepare, execute, and clean up a workload."""

    name: str
    version: str
    supported_devices: tuple[str, ...]
    supported_precisions: tuple[str, ...]

    def supports_device(self, device: str) -> bool:
        """Return whether the backend can target the requested device string."""

    def validate(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> None:
        """Validate the backend against the selected configuration and hardware."""

    def prepare(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        """Prepare backend resources before the benchmark starts."""

    def execute(
        self,
        phase: ExecutionPhase,
        iteration: int,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        """Run one warmup or measured iteration and return backend observations."""

    def cleanup(self) -> None:
        """Release any resources acquired during preparation."""


@runtime_checkable
class HardwareInspector(Protocol):
    """Collect host and target hardware metadata for a benchmark session."""

    def inspect(self) -> HardwareProfile:
        """Return a hardware profile for the current machine."""


@runtime_checkable
class BackendRegistry(Protocol):
    """Resolve and validate benchmark backends."""

    def register(self, backend: BenchmarkBackend) -> None:
        """Register a backend implementation."""

    def resolve(self, name: str) -> BenchmarkBackend:
        """Return a backend by registry name."""

    def select(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None = None,
    ) -> BenchmarkBackend:
        """Select the best backend for the resolved configuration and hardware."""

    def validate(
        self,
        backend: BenchmarkBackend,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None = None,
    ) -> None:
        """Validate a backend for the requested configuration and hardware."""


@runtime_checkable
class MetricProvider(Protocol):
    """Compute metrics from benchmark runs and captured observations."""

    name: str
    version: str
    required_observations: tuple[str, ...]

    def compute(
        self,
        configuration: Configuration,
        runs: tuple[ExecutionResult, ...],
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> tuple[Metric, ...]:
        """Return metrics produced from the supplied benchmark session context."""


@runtime_checkable
class Reporter(Protocol):
    """Render a report view into one durable artifact format."""

    format: str
    extension: str

    def render(self, view: Any) -> str:
        """Return the serialized report payload."""


@runtime_checkable
class Visualizer(Protocol):
    """Build a dashboard-ready chart specification from a benchmark session."""

    family: str
    title: str

    def build(self, session: Any) -> Any:
        """Return a chart specification for the supplied session."""
