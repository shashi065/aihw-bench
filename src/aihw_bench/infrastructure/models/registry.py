"""Registry and built-in model loaders for supported runtime formats."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from aihw_bench.domain.errors import ModelError
from aihw_bench.domain.model_support import (
    LoadedModel,
    ModelLoader,
    ModelLoaderCatalog,
    ModelLoadRequest,
)
from aihw_bench.domain.models import ModelMetadata, WorkloadConfig


def _normalize_extension(path: Path) -> str:
    return path.suffix.lower()


def _as_int_shape(shape: Sequence[Any] | Any) -> list[int]:
    if shape is None:
        return []
    if isinstance(shape, Sequence) and not isinstance(shape, str | bytes):
        result: list[int] = []
        for dimension in shape:
            if isinstance(dimension, bool):
                result.append(int(dimension))
            elif isinstance(dimension, int):
                result.append(dimension)
            else:
                try:
                    result.append(int(dimension))
                except (TypeError, ValueError):
                    result.append(-1)
        return result
    return []


def _batch_sizes_from_shapes(shapes: Iterable[Sequence[int]]) -> list[int]:
    batch_sizes = {
        shape[0] for shape in shapes if shape and isinstance(shape[0], int) and shape[0] > 0
    }
    return sorted(batch_sizes)


def _tensor_records(
    details: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    tensor_records: list[dict[str, Any]] = []
    shape_map: dict[str, list[int]] = {}
    for detail in details:
        name = str(
            detail.get("name") or detail.get("debugName") or detail.get("tensor_name") or "tensor"
        )
        shape = _as_int_shape(detail.get("shape") or detail.get("dims") or detail.get("sizes"))
        tensor_type = detail.get("dtype") or detail.get("type") or detail.get("data_type")
        if tensor_type is not None:
            tensor_type = str(tensor_type)
        tensor_records.append({"name": name, "shape": shape, "dtype": tensor_type})
        shape_map[name] = shape
    return tensor_records, shape_map


def _missing_dependency_message(package_name: str, extra: str) -> ModelError:
    return ModelError(
        f"Optional model runtime dependency '{package_name}' is not installed.",
        cause=f"Importing {package_name!r} failed.",
        suggestion=extra,
        documentation="docs/developer-guide/model-support.md",
    )


def _load_optional_module(*module_names: str) -> Any:
    last_error: Exception | None = None
    for module_name in module_names:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise ModuleNotFoundError(module_names[0])


class PyTorchModelLoader:
    """Load and validate PyTorch and TorchScript models."""

    name = "pytorch"
    supported_extensions = frozenset({".pt", ".pth", ".ts", ".torchscript"})

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("aihw_bench.model.pytorch")

    def can_load(self, source: Path) -> bool:
        return _normalize_extension(source) in self.supported_extensions

    def load(self, request: ModelLoadRequest) -> LoadedModel:
        source = self._validate_source(request.source)
        torch = self._import_torch()
        self.logger.info("Loading PyTorch model from %s", source)

        handle: Any
        format_name = "pytorch"
        try:
            handle = torch.jit.load(str(source), map_location="cpu")
            format_name = "torchscript"
        except Exception:
            try:
                handle = torch.load(str(source), map_location="cpu")
            except Exception as exc:
                raise ModelError(
                    "PyTorch model could not be loaded.",
                    cause=str(exc),
                    suggestion=(
                        "Verify that the file is a valid TorchScript archive or "
                        "serialized PyTorch model."
                    ),
                    documentation="docs/developer-guide/model-support.md",
                ) from exc

        if isinstance(handle, dict) or not (
            hasattr(handle, "parameters") or hasattr(handle, "graph") or hasattr(handle, "forward")
        ):
            raise ModelError(
                "PyTorch model is not a supported module object.",
                cause="The loaded object is a state dictionary or incompatible container.",
                suggestion="Load a TorchScript model or a serialized nn.Module instance.",
                documentation="docs/developer-guide/model-support.md",
            )

        metadata = self._metadata(
            source=source,
            request=request,
            handle=handle,
            framework="pytorch",
            format_name=format_name,
        )
        return LoadedModel(source=source, loader_name=self.name, metadata=metadata, handle=handle)

    def _import_torch(self) -> Any:
        try:
            return _load_optional_module("torch")
        except ModuleNotFoundError as exc:
            raise _missing_dependency_message(
                "torch",
                "Install the optional 'pytorch' extra to load PyTorch and TorchScript models.",
            ) from exc

    def _validate_source(self, source: Path) -> Path:
        if not source.exists():
            raise ModelError(
                "Model file does not exist.",
                cause=f"{source} was not found.",
                suggestion="Provide an existing PyTorch model path.",
                documentation="docs/developer-guide/model-support.md",
            )
        if not source.is_file():
            raise ModelError(
                "Model source is not a file.",
                cause=f"{source} is not a regular file.",
                suggestion="Provide a model file path.",
                documentation="docs/developer-guide/model-support.md",
            )
        if not self.can_load(source):
            raise ModelError(
                "Unsupported PyTorch model format.",
                cause=f"{source.suffix or '<no extension>'} is not a supported PyTorch extension.",
                suggestion="Use a .pt, .pth, .ts, or .torchscript file.",
                documentation="docs/developer-guide/model-support.md",
            )
        return source

    def _metadata(
        self,
        *,
        source: Path,
        request: ModelLoadRequest,
        handle: Any,
        framework: str,
        format_name: str,
    ) -> ModelMetadata:
        input_tensors, input_shapes = self._tensor_info_from_torch(handle, "inputs")
        output_tensors, output_shapes = self._tensor_info_from_torch(handle, "outputs")
        parameters = self._count_parameters(handle)
        precision = request.precision
        supported_precision = [precision] if precision else []
        supported_batch_sizes = _batch_sizes_from_shapes(input_shapes.values())
        return ModelMetadata(
            model_id=request.name or source.stem,
            name=request.name or source.stem,
            format=format_name,
            framework=framework,
            source=str(source),
            size_bytes=source.stat().st_size,
            input_shapes={
                **{key: list(value) for key, value in request.input_shapes.items()},
                **input_shapes,
            },
            output_shapes=output_shapes,
            input_tensors=input_tensors,
            output_tensors=output_tensors,
            precision=precision,
            supported_precision=supported_precision,
            supported_batch_sizes=supported_batch_sizes,
            parameters=parameters,
            metadata=dict(request.metadata),
        )

    @staticmethod
    def _count_parameters(handle: Any) -> int | None:
        parameters = getattr(handle, "parameters", None)
        if not callable(parameters):
            return None
        total = 0
        seen = False
        try:
            for parameter in parameters():
                seen = True
                if hasattr(parameter, "numel"):
                    total += int(parameter.numel())
            return total if seen else None
        except Exception:
            return None

    @staticmethod
    def _tensor_info_from_torch(
        handle: Any, direction: str
    ) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
        graph = getattr(handle, "graph", None)
        if graph is None:
            return [], {}
        items: Sequence[Any] = getattr(graph, direction, lambda: [])()
        details: list[Mapping[str, Any]] = []
        for item in items:
            tensor_type = None
            if hasattr(item, "type") and callable(item.type):
                tensor_type = item.type()
            size = None
            if tensor_type is not None:
                tensor_sizes = getattr(tensor_type, "sizes", None)
                size = tensor_sizes() if callable(tensor_sizes) else tensor_sizes
            debug_name = getattr(item, "debugName", None)
            name = debug_name() if callable(debug_name) else str(item)
            scalar_type = getattr(tensor_type, "scalarType", None)
            dtype = scalar_type() if callable(scalar_type) else None
            details.append(
                {
                    "name": name,
                    "shape": size,
                    "dtype": dtype,
                }
            )
        return _tensor_records(details)


class OnnxRuntimeModelLoader:
    """Load ONNX models through ONNX Runtime."""

    name = "onnxruntime"
    supported_extensions = frozenset({".onnx"})

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("aihw_bench.model.onnxruntime")

    def can_load(self, source: Path) -> bool:
        return _normalize_extension(source) in self.supported_extensions

    def load(self, request: ModelLoadRequest) -> LoadedModel:
        source = self._validate_source(request.source)
        onnxruntime = self._import_onnxruntime()
        self.logger.info("Loading ONNX model from %s", source)

        try:
            session = onnxruntime.InferenceSession(str(source), providers=["CPUExecutionProvider"])
        except Exception as exc:
            raise ModelError(
                "ONNX model could not be loaded.",
                cause=str(exc),
                suggestion=(
                    "Verify that the file is a valid ONNX graph and that ONNX Runtime "
                    "is installed."
                ),
                documentation="docs/developer-guide/model-support.md",
            ) from exc

        input_tensors, input_shapes = self._tensor_info_from_onnx(session.get_inputs())
        output_tensors, output_shapes = self._tensor_info_from_onnx(session.get_outputs())
        metadata = session.get_modelmeta()
        model_name = request.name or getattr(metadata, "graph_name", None) or source.stem
        precision = request.precision
        if precision is None:
            precision = self._precision_from_tensor_types([*input_tensors, *output_tensors])
        supported_precision = [precision] if precision else []
        parameters = self._int_metadata(metadata, ("parameter_count", "parameters"))
        if parameters is None:
            parameters = self._int_metadata(
                getattr(metadata, "custom_metadata_map", {}), ("parameter_count", "parameters")
            )
        metadata_model = ModelMetadata(
            model_id=model_name,
            name=model_name,
            format="onnx",
            framework="onnxruntime",
            source=str(source),
            size_bytes=source.stat().st_size,
            input_shapes={
                **{key: list(value) for key, value in request.input_shapes.items()},
                **input_shapes,
            },
            output_shapes=output_shapes,
            input_tensors=input_tensors,
            output_tensors=output_tensors,
            precision=precision,
            supported_precision=supported_precision,
            supported_batch_sizes=_batch_sizes_from_shapes(input_shapes.values()),
            parameters=parameters,
            metadata={
                **dict(request.metadata),
                "producer_name": getattr(metadata, "producer_name", None),
                "graph_name": getattr(metadata, "graph_name", None),
            },
        )
        return LoadedModel(
            source=source, loader_name=self.name, metadata=metadata_model, handle=session
        )

    def _import_onnxruntime(self) -> Any:
        try:
            return _load_optional_module("onnxruntime")
        except ModuleNotFoundError as exc:
            raise _missing_dependency_message(
                "onnxruntime",
                "Install the optional 'onnx' extra to load ONNX models.",
            ) from exc

    def _validate_source(self, source: Path) -> Path:
        if not source.exists():
            raise ModelError(
                "Model file does not exist.",
                cause=f"{source} was not found.",
                suggestion="Provide an existing ONNX model path.",
                documentation="docs/developer-guide/model-support.md",
            )
        if not source.is_file():
            raise ModelError(
                "Model source is not a file.",
                cause=f"{source} is not a regular file.",
                suggestion="Provide a model file path.",
                documentation="docs/developer-guide/model-support.md",
            )
        if not self.can_load(source):
            raise ModelError(
                "Unsupported ONNX model format.",
                cause=f"{source.suffix or '<no extension>'} is not a supported ONNX extension.",
                suggestion="Use a .onnx file.",
                documentation="docs/developer-guide/model-support.md",
            )
        return source

    @staticmethod
    def _tensor_info_from_onnx(
        details: Sequence[Any],
    ) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
        records: list[dict[str, Any]] = []
        shapes: dict[str, list[int]] = {}
        for detail in details:
            name = getattr(detail, "name", "tensor")
            shape = _as_int_shape(getattr(detail, "shape", []))
            dtype = getattr(detail, "type", None)
            tensor_name = str(name)
            records.append({"name": tensor_name, "shape": shape, "dtype": dtype})
            shapes[tensor_name] = shape
        return records, shapes

    @staticmethod
    def _precision_from_tensor_types(tensors: Sequence[Mapping[str, Any]]) -> str | None:
        for tensor in tensors:
            tensor_type = str(tensor.get("dtype") or "").lower()
            if "float16" in tensor_type or "fp16" in tensor_type:
                return "fp16"
            if "float32" in tensor_type or "fp32" in tensor_type or "float" in tensor_type:
                return "fp32"
            if "int8" in tensor_type:
                return "int8"
        return None

    @staticmethod
    def _int_metadata(metadata: Any, keys: Sequence[str]) -> int | None:
        if metadata is None:
            return None
        if hasattr(metadata, "get"):
            for key in keys:
                value = metadata.get(key)
                try:
                    if value is not None:
                        return int(value)
                except (TypeError, ValueError):
                    continue
        return None


class TensorFlowLiteModelLoader:
    """Load TensorFlow Lite models using the runtime interpreter."""

    name = "tflite"
    supported_extensions = frozenset({".tflite"})

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("aihw_bench.model.tflite")

    def can_load(self, source: Path) -> bool:
        return _normalize_extension(source) in self.supported_extensions

    def load(self, request: ModelLoadRequest) -> LoadedModel:
        source = self._validate_source(request.source)
        interpreter = self._import_interpreter()
        self.logger.info("Loading TensorFlow Lite model from %s", source)

        try:
            model = interpreter.Interpreter(model_path=str(source))
            model.allocate_tensors()
        except Exception as exc:
            raise ModelError(
                "TensorFlow Lite model could not be initialized.",
                cause=str(exc),
                suggestion=(
                    "Verify that the file is a valid .tflite model and the runtime "
                    "interpreter is installed."
                ),
                documentation="docs/developer-guide/model-support.md",
            ) from exc

        input_tensors, input_shapes = self._tensor_info_from_tflite(model.get_input_details())
        output_tensors, output_shapes = self._tensor_info_from_tflite(model.get_output_details())
        precision = request.precision or self._precision_from_tensor_types(
            [*input_tensors, *output_tensors]
        )
        metadata = ModelMetadata(
            model_id=request.name or source.stem,
            name=request.name or source.stem,
            format="tflite",
            framework="tensorflow-lite",
            source=str(source),
            size_bytes=source.stat().st_size,
            input_shapes={
                **{key: list(value) for key, value in request.input_shapes.items()},
                **input_shapes,
            },
            output_shapes=output_shapes,
            input_tensors=input_tensors,
            output_tensors=output_tensors,
            precision=precision,
            supported_precision=[precision] if precision else [],
            supported_batch_sizes=_batch_sizes_from_shapes(input_shapes.values()),
            metadata=dict(request.metadata),
        )
        return LoadedModel(source=source, loader_name=self.name, metadata=metadata, handle=model)

    def _import_interpreter(self) -> Any:
        try:
            return _load_optional_module("tflite_runtime.interpreter", "tensorflow.lite")
        except ModuleNotFoundError as exc:
            raise _missing_dependency_message(
                "tflite-runtime",
                (
                    "Install the optional 'tflite' extra or TensorFlow Lite runtime "
                    "support for .tflite models."
                ),
            ) from exc

    def _validate_source(self, source: Path) -> Path:
        if not source.exists():
            raise ModelError(
                "Model file does not exist.",
                cause=f"{source} was not found.",
                suggestion="Provide an existing TensorFlow Lite model path.",
                documentation="docs/developer-guide/model-support.md",
            )
        if not source.is_file():
            raise ModelError(
                "Model source is not a file.",
                cause=f"{source} is not a regular file.",
                suggestion="Provide a model file path.",
                documentation="docs/developer-guide/model-support.md",
            )
        if not self.can_load(source):
            raise ModelError(
                "Unsupported TensorFlow Lite model format.",
                cause=(
                    f"{source.suffix or '<no extension>'} is not a supported "
                    "TensorFlow Lite extension."
                ),
                suggestion="Use a .tflite file.",
                documentation="docs/developer-guide/model-support.md",
            )
        return source

    @staticmethod
    def _tensor_info_from_tflite(
        details: Sequence[Mapping[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
        records: list[dict[str, Any]] = []
        shapes: dict[str, list[int]] = {}
        for detail in details:
            name = str(detail.get("name") or "tensor")
            shape = _as_int_shape(detail.get("shape") or detail.get("dims") or [])
            dtype = detail.get("dtype")
            records.append(
                {"name": name, "shape": shape, "dtype": str(dtype) if dtype is not None else None}
            )
            shapes[name] = shape
        return records, shapes

    @staticmethod
    def _precision_from_tensor_types(tensors: Sequence[Mapping[str, Any]]) -> str | None:
        for tensor in tensors:
            tensor_type = str(tensor.get("dtype") or "").lower()
            if "float16" in tensor_type or "fp16" in tensor_type:
                return "fp16"
            if "float32" in tensor_type or "fp32" in tensor_type or "float" in tensor_type:
                return "fp32"
            if "int8" in tensor_type:
                return "int8"
        return None


class ModelLoaderRegistry(ModelLoaderCatalog):
    """Registry of format-specific model loaders."""

    def __init__(
        self, loaders: Iterable[ModelLoader] | None = None, *, logger: logging.Logger | None = None
    ) -> None:
        self.logger = logger or logging.getLogger("aihw_bench.model.registry")
        self._loaders: dict[str, ModelLoader] = {}
        if loaders is None:
            loaders = [PyTorchModelLoader(), OnnxRuntimeModelLoader(), TensorFlowLiteModelLoader()]
        for loader in loaders:
            self.register(loader)

    def register(self, loader: ModelLoader) -> None:
        """Register a loader by name."""
        self._loaders[loader.name] = loader

    def load(self, request: ModelLoadRequest) -> LoadedModel:
        """Load a model by request, resolving the best matching loader."""
        source = request.source
        loader = self._resolve_loader(source, request.framework)
        self.logger.info("Using %s loader for %s", loader.name, source)
        return loader.load(request)

    def load_workload(self, workload: WorkloadConfig) -> LoadedModel:
        """Load a model from resolved configuration."""
        if workload.source is None:
            raise ModelError(
                "Workload configuration does not define a model source.",
                cause="The resolved workload has no source path.",
                suggestion=(
                    "Set workload.source in the configuration or provide a resolved "
                    "model directly."
                ),
                documentation="docs/developer-guide/model-support.md",
            )
        request = ModelLoadRequest(
            source=Path(workload.source),
            name=workload.name,
            input_shapes=workload.input_shapes,
            metadata=workload.metadata,
        )
        return self.load(request)

    def _resolve_loader(self, source: Path, framework: str | None) -> ModelLoader:
        if framework is not None:
            for loader in self._loaders.values():
                if loader.name == framework:
                    return loader
            raise ModelError(
                "Requested model framework is not supported.",
                cause=f"No registered loader named {framework!r}.",
                suggestion="Use a registered framework name or install the corresponding adapter.",
                documentation="docs/developer-guide/model-support.md",
            )

        for loader in self._loaders.values():
            if loader.can_load(source):
                return loader

        supported = ", ".join(sorted(self._loaders)) or "none"
        raise ModelError(
            "Unsupported model format.",
            cause=f"{source.suffix or '<no extension>'} does not match any registered loader.",
            suggestion=f"Register a loader for the format or use one of: {supported}.",
            documentation="docs/developer-guide/model-support.md",
        )
