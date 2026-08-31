"""Reference backend used for benchmark engine validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from aihw_bench._version import __version__
from aihw_bench.domain.errors import BackendError
from aihw_bench.domain.models import Configuration, ExecutionPhase, HardwareProfile, ModelMetadata


@dataclass(slots=True)
class ReferenceBenchmarkBackend:
    """A deterministic in-process backend for engine validation and tests."""

    name: str = "reference"
    version: str = __version__
    supported_devices: tuple[str, ...] = ("cpu",)
    supported_precisions: tuple[str, ...] = ("fp32",)
    metadata: dict[str, Any] = field(default_factory=dict)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def supports_device(self, device: str) -> bool:
        return device.strip().lower().startswith("cpu")

    def validate(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> None:
        if not self.supports_device(configuration.backend.device):
            raise BackendError(f"Reference backend cannot target {configuration.backend.device!r}.")

    def prepare(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        self.calls.append(
            {
                "operation": "prepare",
                "backend": self.name,
                "precision": configuration.execution.precision,
                "device": configuration.backend.device,
                "workload": workload.model_id if workload is not None else None,
            }
        )
        return {"backend": self.name, "version": self.version, **self.metadata}

    def execute(
        self,
        phase: ExecutionPhase,
        iteration: int,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        payload = {
            "operation": "execute",
            "phase": phase.value,
            "iteration": iteration,
            "backend": self.name,
            "device": configuration.backend.device,
            "precision": configuration.execution.precision,
            "workload": workload.model_id if workload is not None else None,
        }
        self.calls.append(payload)
        return {
            "phase": phase.value,
            "iteration": iteration,
            "backend": self.name,
            "device": configuration.backend.device,
            "precision": configuration.execution.precision,
            **self.metadata,
        }

    def cleanup(self) -> None:
        self.calls.append({"operation": "cleanup", "backend": self.name})
