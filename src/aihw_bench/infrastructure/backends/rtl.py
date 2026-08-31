"""RTL simulator backend with normalized cycle and waveform observations."""

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
class RtlSimulatorBackend(BenchmarkBackend):
    """Adapter contract for externally run RTL simulators.

    It does not invoke simulator binaries. Integrations pass normalized observations
    through ``backend.options`` so sessions retain cycle and waveform provenance.
    """

    name: str = "rtl"
    version: str = "1.2.0"
    supported_devices: tuple[str, ...] = ("rtl", "simulator")
    supported_precisions: tuple[str, ...] = ("fp32", "int8")
    calls: list[dict[str, Any]] = field(default_factory=list)

    def supports_device(self, device: str) -> bool:
        return normalize_backend_token(device).startswith(("rtl", "simulator"))

    def validate(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> None:
        if not self.supports_device(configuration.backend.device):
            raise BackendError(
                "RTL backend cannot target the requested device.",
                cause=(
                    f"Requested device {configuration.backend.device!r} is not "
                    "an RTL simulator target."
                ),
                suggestion="Use rtl or simulator as the device, or select another backend.",
                documentation=BACKEND_SUPPORT_DOC,
            )
        if configuration.execution.precision not in self.supported_precisions:
            raise BackendError(
                "RTL backend precision is not supported.",
                cause=(
                    f"RTL simulation supports {', '.join(self.supported_precisions)} "
                    "metadata precision."
                ),
                suggestion="Use fp32 or int8, or configure an integration-specific plugin.",
                documentation=BACKEND_SUPPORT_DOC,
            )

    def prepare(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        self.validate(configuration, hardware, workload)
        simulator = {**hardware.simulator, **configuration.backend.options.get("simulator", {})}
        self.calls.append({"operation": "prepare", "simulator": simulator.get("name")})
        return {"backend": self.name, "version": self.version, "simulator": simulator}

    def execute(
        self,
        phase: ExecutionPhase,
        iteration: int,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        self.validate(configuration, hardware, workload)
        observations = dict(configuration.backend.options.get("rtl_observations", {}))
        observations.update({"phase": phase.value, "iteration": iteration, "backend": self.name})
        self.calls.append({"operation": "execute", "phase": phase.value, "iteration": iteration})
        return observations

    def cleanup(self) -> None:
        self.calls.append({"operation": "cleanup"})
