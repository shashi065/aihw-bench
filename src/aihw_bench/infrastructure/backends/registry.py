"""Backend registry and selection helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from aihw_bench.domain.errors import BackendError
from aihw_bench.domain.models import Configuration, HardwareProfile, ModelMetadata
from aihw_bench.domain.ports import BackendRegistry, BenchmarkBackend


@dataclass
class BackendRegistryImpl(BackendRegistry):
    """Register, resolve, select, and validate benchmark backends."""

    backends: dict[str, BenchmarkBackend] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("aihw_bench.backends"))

    def register(self, backend: BenchmarkBackend) -> None:
        self.backends[backend.name] = backend

    def resolve(self, name: str) -> BenchmarkBackend:
        try:
            return self.backends[name]
        except KeyError as exc:
            raise BackendError(
                "Backend is not registered.",
                cause=f"No backend named {name!r} exists in the registry.",
                suggestion="Register the backend or choose a supported backend name.",
                documentation="docs/developer-guide/backend-support.md",
            ) from exc

    def select(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None = None,
    ) -> BenchmarkBackend:
        desired_name = configuration.backend.name or "cpu"
        if desired_name in self.backends:
            backend = self.backends[desired_name]
            self.validate(backend, configuration, hardware, workload)
            return backend

        for backend in self.backends.values():
            if backend.supports_device(configuration.backend.device):
                self.validate(backend, configuration, hardware, workload)
                return backend

        raise BackendError(
            "No backend matched the requested configuration.",
            cause=(
                f"Backend name {desired_name!r} and device "
                f"{configuration.backend.device!r} could not be resolved."
            ),
            suggestion="Register a matching backend or choose a supported device.",
            documentation="docs/developer-guide/backend-support.md",
        )

    def validate(
        self,
        backend: BenchmarkBackend,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None = None,
    ) -> None:
        backend.validate(configuration, hardware, workload)


def default_backend_registry() -> BackendRegistryImpl:
    """Create the built-in registry with CPU and GPU backends."""
    from aihw_bench.infrastructure.backends.cpu import CPUBackend
    from aihw_bench.infrastructure.backends.fpga import FpgaPlaceholderBackend
    from aihw_bench.infrastructure.backends.gpu import GPUBackend
    from aihw_bench.infrastructure.backends.rtl import RtlSimulatorBackend

    registry = BackendRegistryImpl()
    registry.register(CPUBackend())
    registry.register(GPUBackend())
    registry.register(RtlSimulatorBackend())
    registry.register(FpgaPlaceholderBackend())
    return registry
