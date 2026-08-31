"""Built-in benchmark backends."""

from aihw_bench.infrastructure.backends.cpu import CPUBackend
from aihw_bench.infrastructure.backends.fpga import FpgaPlaceholderBackend
from aihw_bench.infrastructure.backends.gpu import GPUBackend
from aihw_bench.infrastructure.backends.reference import ReferenceBenchmarkBackend
from aihw_bench.infrastructure.backends.registry import (
    BackendRegistryImpl,
    default_backend_registry,
)
from aihw_bench.infrastructure.backends.rtl import RtlSimulatorBackend

__all__ = [
    "BackendRegistryImpl",
    "CPUBackend",
    "FpgaPlaceholderBackend",
    "GPUBackend",
    "ReferenceBenchmarkBackend",
    "RtlSimulatorBackend",
    "default_backend_registry",
]
