"""Model loading adapters for AIHW-Bench."""

from aihw_bench.infrastructure.models.registry import (
    ModelLoaderRegistry,
    OnnxRuntimeModelLoader,
    PyTorchModelLoader,
    TensorFlowLiteModelLoader,
)

__all__ = [
    "ModelLoaderRegistry",
    "OnnxRuntimeModelLoader",
    "PyTorchModelLoader",
    "TensorFlowLiteModelLoader",
]
