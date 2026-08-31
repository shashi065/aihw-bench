"""FPGA placeholder backend for capability validation and plugin handoff."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from aihw_bench.domain.errors import BackendError
from aihw_bench.domain.models import Configuration, ExecutionPhase, HardwareProfile, ModelMetadata
from aihw_bench.domain.ports import BenchmarkBackend
from aihw_bench.infrastructure.backends.validation import (
    BACKEND_SUPPORT_DOC,
    normalize_backend_token,
)


@dataclass(slots=True)
class FpgaPlaceholderBackend(BenchmarkBackend):
    """Validate FPGA-targeted configurations until a board-specific plugin is installed."""

    name: str = "fpga"
    version: str = "1.2.0"
    supported_devices: tuple[str, ...] = ("fpga",)
    supported_precisions: tuple[str, ...] = ("fp32", "int8")
    calls: list[dict[str, Any]] = field(default_factory=list)

    def supports_device(self, device: str) -> bool:
        return normalize_backend_token(device).startswith("fpga")

    def validate(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> None:
        if not self.supports_device(configuration.backend.device):
            raise BackendError(
                "FPGA backend cannot target the requested device.",
                cause=f"Requested device {configuration.backend.device!r} is not FPGA compatible.",
                suggestion="Use an fpga target or select a board-specific plugin.",
                documentation=BACKEND_SUPPORT_DOC,
            )

    def prepare(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        self.validate(configuration, hardware, workload)
        raise BackendError(
            "FPGA execution requires a board-specific plugin.",
            cause=(
                "The built-in FPGA backend is a capability placeholder and "
                "does not include vendor toolchains."
            ),
            suggestion="Install an FPGA plugin for the target board and runtime.",
            documentation=BACKEND_SUPPORT_DOC,
        )

    def execute(
        self,
        phase: ExecutionPhase,
        iteration: int,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        raise AssertionError("FPGA execution is unavailable before prepare succeeds.")

    def cleanup(self) -> None:
        self.calls.append({"operation": "cleanup"})
