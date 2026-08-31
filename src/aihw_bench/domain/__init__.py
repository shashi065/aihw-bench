"""Domain models and contracts for AIHW-Bench."""

from aihw_bench.domain.errors import (
    AihwBenchError,
    ConfigurationError,
    ModelError,
    RuntimeExecutionError,
    SecurityError,
    SessionError,
    ValidationError,
)
from aihw_bench.domain.model_support import (
    LoadedModel,
    ModelLoader,
    ModelLoaderCatalog,
    ModelLoadRequest,
)
from aihw_bench.domain.models import (
    BenchmarkResult,
    BenchmarkSession,
    Configuration,
    Diagnostic,
    ExecutionResult,
    ExportArtifact,
    HardwareProfile,
    Metric,
    ModelMetadata,
    PluginMetadata,
    Profile,
    RunHistory,
)
from aihw_bench.domain.ports import (
    BackendRegistry,
    BenchmarkBackend,
    HardwareInspector,
    MetricProvider,
    Reporter,
)

__all__ = [
    "AihwBenchError",
    "BackendRegistry",
    "BenchmarkBackend",
    "BenchmarkResult",
    "BenchmarkSession",
    "Configuration",
    "ConfigurationError",
    "Diagnostic",
    "ExecutionResult",
    "ExportArtifact",
    "HardwareInspector",
    "HardwareProfile",
    "LoadedModel",
    "Metric",
    "MetricProvider",
    "ModelError",
    "ModelLoadRequest",
    "ModelLoader",
    "ModelLoaderCatalog",
    "ModelMetadata",
    "PluginMetadata",
    "Profile",
    "Reporter",
    "RunHistory",
    "RuntimeExecutionError",
    "SecurityError",
    "SessionError",
    "ValidationError",
]
