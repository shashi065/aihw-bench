"""Infrastructure adapters for AIHW-Bench."""

from aihw_bench.infrastructure.backends import (
    BackendRegistryImpl,
    CPUBackend,
    GPUBackend,
    ReferenceBenchmarkBackend,
    default_backend_registry,
)
from aihw_bench.infrastructure.hardware import SystemHardwareInspector
from aihw_bench.infrastructure.models import (
    ModelLoaderRegistry,
    OnnxRuntimeModelLoader,
    PyTorchModelLoader,
    TensorFlowLiteModelLoader,
)

__all__ = [
    "BackendRegistryImpl",
    "CPUBackend",
    "GPUBackend",
    "ModelLoaderRegistry",
    "OnnxRuntimeModelLoader",
    "PyTorchModelLoader",
    "ReferenceBenchmarkBackend",
    "SystemHardwareInspector",
    "TensorFlowLiteModelLoader",
    "default_backend_registry",
]
