"""CPU backend implementation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from aihw_bench._version import __version__
from aihw_bench.domain.errors import BackendError
from aihw_bench.domain.models import Configuration, ExecutionPhase, HardwareProfile, ModelMetadata
from aihw_bench.domain.ports import BenchmarkBackend
from aihw_bench.infrastructure.backends.validation import (
    BACKEND_SUPPORT_DOC,
    normalize_backend_token,
    validate_precision,
)


@dataclass(slots=True)
class CPUBackend(BenchmarkBackend):
    """CPU reference backend for production validation and tests."""

    name: str = "cpu"
    version: str = __version__
    supported_devices: tuple[str, ...] = ("cpu",)
    supported_precisions: tuple[str, ...] = ("fp32", "fp16", "int8")
    metadata: dict[str, Any] = field(default_factory=dict)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def supports_device(self, device: str) -> bool:
        return normalize_backend_token(device).startswith("cpu")

    def validate(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> None:
        if not self.supports_device(configuration.backend.device):
            raise BackendError(
                "CPU backend cannot target the requested device.",
                cause=f"Requested device {configuration.backend.device!r} is not CPU compatible.",
                suggestion=(
                    "Choose a CPU device or select a backend that matches the requested target."
                ),
                documentation=BACKEND_SUPPORT_DOC,
            )
        validate_precision(
            backend_name=self.name,
            supported_precisions=self.supported_precisions,
            requested_precision=configuration.execution.precision,
        )

    def prepare(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        self.validate(configuration, hardware, workload)
        self.calls.append({"operation": "prepare", "device": configuration.backend.device})
        return {
            "backend": self.name,
            "version": self.version,
            "device": configuration.backend.device,
            "hardware": hardware.summary(),
            **self.metadata,
        }

    def execute(
        self,
        phase: ExecutionPhase,
        iteration: int,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        self.validate(configuration, hardware, workload)
        self.calls.append({"operation": "execute", "phase": phase.value, "iteration": iteration})
        return {
            "phase": phase.value,
            "iteration": iteration,
            "backend": self.name,
            "device": configuration.backend.device,
            "precision": configuration.execution.precision,
            "workload": workload.model_id if workload is not None else None,
            **self.metadata,
        }

    def cleanup(self) -> None:
        self.calls.append({"operation": "cleanup"})
