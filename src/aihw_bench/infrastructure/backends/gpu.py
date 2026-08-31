"""GPU backend implementation and capability validation."""

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
class GPUBackend(BenchmarkBackend):
    """GPU backend that validates accelerator availability before execution."""

    name: str = "gpu"
    version: str = __version__
    supported_devices: tuple[str, ...] = ("gpu", "cuda", "rocm", "hip", "intel-gpu", "xpu")
    supported_precisions: tuple[str, ...] = ("fp32", "fp16", "int8")
    metadata: dict[str, Any] = field(default_factory=dict)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def supports_device(self, device: str) -> bool:
        normalized = normalize_backend_token(device)
        return normalized.startswith(("gpu", "cuda", "rocm", "hip", "intel-gpu", "xpu"))

    def validate(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> None:
        if not self.supports_device(configuration.backend.device):
            raise BackendError(
                "GPU backend cannot target the requested device.",
                cause=f"Requested device {configuration.backend.device!r} is not GPU compatible.",
                suggestion="Choose a CUDA, ROCm, Intel GPU, or generic GPU device target.",
                documentation=BACKEND_SUPPORT_DOC,
            )
        validate_precision(
            backend_name=self.name,
            supported_precisions=self.supported_precisions,
            requested_precision=configuration.execution.precision,
        )
        capability = hardware.capability_report()["gpu"]
        if not capability["available"]:
            raise BackendError(
                "GPU hardware is not available.",
                cause="No GPU accelerator was detected on the current host.",
                suggestion="Run on a machine with a supported GPU or select the CPU backend.",
                documentation=BACKEND_SUPPORT_DOC,
            )
        requested = _requested_capability(configuration.backend.device)
        available = set(capability["capabilities"])
        if requested is not None and requested not in available:
            detected = (
                ", ".join(sorted(available)) or "GPU detected but no supported runtime is available"
            )
            raise BackendError(
                "Requested GPU target is not available.",
                cause=(f"Requested {requested!r}, but detected GPU capabilities are: {detected}."),
                suggestion="Select a compatible device target or install the matching GPU runtime.",
                documentation=BACKEND_SUPPORT_DOC,
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


def _requested_capability(device: str) -> str | None:
    """Return the concrete runtime capability required by a device token."""
    normalized = normalize_backend_token(device)
    if normalized.startswith("cuda"):
        return "cuda"
    if normalized.startswith(("rocm", "hip")):
        return "rocm"
    if normalized.startswith(("intel-gpu", "xpu")):
        return "intel-gpu"
    return None
