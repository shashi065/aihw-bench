from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest
from tests.conftest import FakeModelLoader

import aihw_bench.infrastructure.models.registry as registry_module
from aihw_bench.domain.errors import ModelError
from aihw_bench.domain.model_support import ModelLoadRequest
from aihw_bench.domain.models import ModelMetadata, WorkloadConfig
from aihw_bench.infrastructure.models import (
    ModelLoaderRegistry,
    OnnxRuntimeModelLoader,
    PyTorchModelLoader,
    TensorFlowLiteModelLoader,
)

EXPECTED_TORCH_PARAMETERS = 10
EXPECTED_ONNX_PARAMETERS = 42


def test_model_metadata_fingerprint_is_stable() -> None:
    metadata = ModelMetadata(
        model_id="demo",
        name="Demo",
        format="onnx",
        framework="onnxruntime",
        supported_precision=["fp32"],
        supported_batch_sizes=[1, 4],
    )

    assert metadata.fingerprint() == metadata.fingerprint()
    assert metadata.to_dict()["framework"] == "onnxruntime"


def test_model_loader_registry_rejects_unsupported_formats(tmp_path: Path) -> None:
    model_file = tmp_path / "model.bin"
    model_file.write_bytes(b"not a supported model")

    with pytest.raises(ModelError, match="Unsupported model format"):
        ModelLoaderRegistry().load(ModelLoadRequest(source=model_file))


def test_model_loader_registry_resolves_explicit_framework(fake_model_file: Path) -> None:
    registry = ModelLoaderRegistry(loaders=[FakeModelLoader()])

    loaded = registry.load(
        ModelLoadRequest(source=fake_model_file, framework="fake-loader", name="named")
    )

    assert loaded.loader_name == "fake-loader"
    assert loaded.metadata.name == "named"


def test_model_loader_registry_rejects_unknown_explicit_framework(fake_model_file: Path) -> None:
    registry = ModelLoaderRegistry(loaders=[FakeModelLoader()])

    with pytest.raises(ModelError, match="framework"):
        registry.load(ModelLoadRequest(source=fake_model_file, framework="missing"))


def test_model_loader_registry_loads_workload(fake_model_file: Path) -> None:
    registry = ModelLoaderRegistry(loaders=[FakeModelLoader()])

    loaded = registry.load_workload(
        WorkloadConfig(
            source=str(fake_model_file),
            name="workload",
            input_shapes={"input": [1, 2]},
            metadata={"format": "fake"},
        )
    )

    assert loaded.metadata.model_id == "workload"
    assert loaded.metadata.input_shapes == {"input": [1, 2]}


def test_model_loader_registry_rejects_workload_without_source() -> None:
    with pytest.raises(ModelError, match="does not define"):
        ModelLoaderRegistry(loaders=[FakeModelLoader()]).load_workload(WorkloadConfig())


def test_pytorch_loader_extracts_metadata_from_fake_torch(monkeypatch, tmp_path: Path) -> None:
    model_file = tmp_path / "model.pt"
    model_file.write_bytes(b"fake torch model")

    class FakeTensorType:
        def sizes(self) -> list[int]:
            return [1, 3, 224, 224]

        def scalarType(self) -> str:  # noqa: N802
            return "Float"

    class FakeGraphItem:
        def __init__(self, name: str) -> None:
            self._name = name

        def debugName(self) -> str:  # noqa: N802
            return self._name

        def type(self) -> FakeTensorType:
            return FakeTensorType()

    class FakeGraph:
        def inputs(self) -> list[FakeGraphItem]:
            return [FakeGraphItem("input")]

        def outputs(self) -> list[FakeGraphItem]:
            return [FakeGraphItem("output")]

    class FakeParameter:
        def numel(self) -> int:
            return 5

    class FakeModel:
        graph = FakeGraph()

        def parameters(self) -> list[FakeParameter]:
            return [FakeParameter(), FakeParameter()]

    fake_torch = SimpleNamespace(
        jit=SimpleNamespace(load=lambda path, map_location=None: FakeModel()),
        load=lambda path, map_location=None: FakeModel(),
    )

    def fake_import_module(name: str):
        if name == "torch":
            return fake_torch
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(
        registry_module.importlib,
        "import_module",
        fake_import_module,
    )

    loaded = PyTorchModelLoader().load(
        ModelLoadRequest(source=model_file, name="demo", precision="fp32")
    )

    assert loaded.metadata.framework == "pytorch"
    assert loaded.metadata.format == "torchscript"
    assert loaded.metadata.parameters == EXPECTED_TORCH_PARAMETERS
    assert loaded.metadata.input_shapes["input"] == [1, 3, 224, 224]
    assert loaded.metadata.supported_batch_sizes == [1]


def test_pytorch_loader_falls_back_from_jit_to_torch_load(monkeypatch, tmp_path: Path) -> None:
    model_file = tmp_path / "model.pth"
    model_file.write_bytes(b"fake torch model")

    class FakeModel:
        def forward(self) -> None:
            return None

    def fail_jit_load(path: str, map_location: str | None = None):
        raise RuntimeError("jit failed")

    fake_torch = SimpleNamespace(
        jit=SimpleNamespace(load=fail_jit_load),
        load=lambda path, map_location=None: FakeModel(),
    )

    def fake_import_module(name: str):
        if name == "torch":
            return fake_torch
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(
        registry_module.importlib,
        "import_module",
        fake_import_module,
    )

    loaded = PyTorchModelLoader().load(ModelLoadRequest(source=model_file))

    assert loaded.metadata.format == "pytorch"


def test_pytorch_loader_rejects_state_dict(monkeypatch, tmp_path: Path) -> None:
    model_file = tmp_path / "model.pt"
    model_file.write_bytes(b"fake torch model")

    def fail_jit_load(path: str, map_location: str | None = None):
        raise RuntimeError("jit failed")

    fake_torch = SimpleNamespace(
        jit=SimpleNamespace(load=fail_jit_load),
        load=lambda path, map_location=None: {"weights": []},
    )

    def fake_import_module(name: str):
        if name == "torch":
            return fake_torch
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(
        registry_module.importlib,
        "import_module",
        fake_import_module,
    )

    with pytest.raises(ModelError, match="not a supported module"):
        PyTorchModelLoader().load(ModelLoadRequest(source=model_file))


def test_pytorch_loader_reports_missing_runtime(monkeypatch, tmp_path: Path) -> None:
    model_file = tmp_path / "model.pt"
    model_file.write_bytes(b"fake torch model")

    def fake_import_module(name: str):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(
        registry_module.importlib,
        "import_module",
        fake_import_module,
    )

    with pytest.raises(ModelError, match="torch"):
        PyTorchModelLoader().load(ModelLoadRequest(source=model_file))


def test_onnx_loader_extracts_metadata_from_fake_session(monkeypatch, tmp_path: Path) -> None:
    model_file = tmp_path / "model.onnx"
    model_file.write_bytes(b"fake onnx model")

    class FakeDetail:
        def __init__(self, name: str, shape: list[int], type_name: str) -> None:
            self.name = name
            self.shape = shape
            self.type = type_name

    class FakeMeta:
        graph_name = "demo-graph"
        producer_name = "unit-test"
        custom_metadata_map: ClassVar[dict[str, str]] = {"parameter_count": "42"}

    class FakeSession:
        def __init__(self, path: str, providers: list[str]) -> None:
            self.path = path
            self.providers = providers

        def get_inputs(self) -> list[FakeDetail]:
            return [FakeDetail("input", [1, 3, 32, 32], "tensor(float)")]

        def get_outputs(self) -> list[FakeDetail]:
            return [FakeDetail("output", [1, 10], "tensor(float)")]

        def get_modelmeta(self) -> FakeMeta:
            return FakeMeta()

    fake_onnxruntime = SimpleNamespace(InferenceSession=FakeSession)

    def fake_import_module(name: str):
        if name == "onnxruntime":
            return fake_onnxruntime
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(
        registry_module.importlib,
        "import_module",
        fake_import_module,
    )

    loaded = OnnxRuntimeModelLoader().load(ModelLoadRequest(source=model_file, name=None))

    assert loaded.metadata.framework == "onnxruntime"
    assert loaded.metadata.format == "onnx"
    assert loaded.metadata.parameters == EXPECTED_ONNX_PARAMETERS
    assert loaded.metadata.supported_precision == ["fp32"]
    assert loaded.metadata.input_tensors[0]["name"] == "input"


def test_onnx_loader_reports_session_initialization_errors(monkeypatch, tmp_path: Path) -> None:
    model_file = tmp_path / "model.onnx"
    model_file.write_bytes(b"fake onnx model")

    def fail_session(path: str, providers: list[str]):
        raise RuntimeError("bad graph")

    fake_onnxruntime = SimpleNamespace(InferenceSession=fail_session)

    def fake_import_module(name: str):
        if name == "onnxruntime":
            return fake_onnxruntime
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(
        registry_module.importlib,
        "import_module",
        fake_import_module,
    )

    with pytest.raises(ModelError, match="could not be loaded"):
        OnnxRuntimeModelLoader().load(ModelLoadRequest(source=model_file))


def test_onnx_loader_precision_and_metadata_helpers() -> None:
    assert (
        OnnxRuntimeModelLoader._precision_from_tensor_types([{"dtype": "tensor(float16)"}])
        == "fp16"
    )
    assert (
        OnnxRuntimeModelLoader._precision_from_tensor_types([{"dtype": "tensor(int8)"}]) == "int8"
    )
    assert OnnxRuntimeModelLoader._precision_from_tensor_types([{"dtype": "tensor(bool)"}]) is None
    assert OnnxRuntimeModelLoader._int_metadata({"parameters": "bad"}, ("parameters",)) is None
    assert OnnxRuntimeModelLoader._int_metadata(None, ("parameters",)) is None


def test_tflite_loader_extracts_metadata_from_fake_interpreter(monkeypatch, tmp_path: Path) -> None:
    model_file = tmp_path / "model.tflite"
    model_file.write_bytes(b"fake tflite model")

    class FakeInterpreter:
        def __init__(self, model_path: str) -> None:
            self.model_path = model_path

        def allocate_tensors(self) -> None:
            return None

        def get_input_details(self) -> list[dict[str, object]]:
            return [{"name": "input", "shape": [1, 16], "dtype": "float32"}]

        def get_output_details(self) -> list[dict[str, object]]:
            return [{"name": "output", "shape": [1, 4], "dtype": "float32"}]

    fake_tflite = SimpleNamespace(Interpreter=FakeInterpreter)

    def fake_import(name: str):
        if name == "tflite_runtime.interpreter":
            raise ModuleNotFoundError(name)
        if name == "tensorflow.lite":
            return fake_tflite
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(registry_module.importlib, "import_module", fake_import)

    loaded = TensorFlowLiteModelLoader().load(ModelLoadRequest(source=model_file, name="demo"))

    assert loaded.metadata.framework == "tensorflow-lite"
    assert loaded.metadata.format == "tflite"
    assert loaded.metadata.supported_batch_sizes == [1]
    assert loaded.metadata.input_shapes["input"] == [1, 16]


def test_tflite_loader_reports_initialization_errors(monkeypatch, tmp_path: Path) -> None:
    model_file = tmp_path / "model.tflite"
    model_file.write_bytes(b"fake tflite model")

    class BrokenInterpreter:
        def __init__(self, model_path: str) -> None:
            self.model_path = model_path

        def allocate_tensors(self) -> None:
            raise RuntimeError("bad tflite")

    fake_tflite = SimpleNamespace(Interpreter=BrokenInterpreter)

    def fake_import_module(name: str):
        if name == "tflite_runtime.interpreter":
            return fake_tflite
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(
        registry_module.importlib,
        "import_module",
        fake_import_module,
    )

    with pytest.raises(ModelError, match="could not be initialized"):
        TensorFlowLiteModelLoader().load(ModelLoadRequest(source=model_file))


@pytest.mark.parametrize(
    ("loader", "filename", "message"),
    [
        (PyTorchModelLoader(), "missing.pt", "does not exist"),
        (OnnxRuntimeModelLoader(), "missing.onnx", "does not exist"),
        (TensorFlowLiteModelLoader(), "missing.tflite", "does not exist"),
    ],
)
def test_model_loaders_reject_missing_files(
    loader,
    filename: str,
    message: str,
    tmp_path: Path,
) -> None:
    with pytest.raises(ModelError, match=message):
        loader.load(ModelLoadRequest(source=tmp_path / filename))


@pytest.mark.parametrize(
    ("loader", "filename"),
    [
        (PyTorchModelLoader(), "model.bin"),
        (OnnxRuntimeModelLoader(), "model.bin"),
        (TensorFlowLiteModelLoader(), "model.bin"),
    ],
)
def test_model_loaders_reject_wrong_extensions(loader, filename: str, tmp_path: Path) -> None:
    model_file = tmp_path / filename
    model_file.write_bytes(b"wrong")

    with pytest.raises(ModelError, match="Unsupported"):
        loader.load(ModelLoadRequest(source=model_file))


@pytest.mark.parametrize(
    ("loader", "dirname"),
    [
        (PyTorchModelLoader(), "model.pt"),
        (OnnxRuntimeModelLoader(), "model.onnx"),
        (TensorFlowLiteModelLoader(), "model.tflite"),
    ],
)
def test_model_loaders_reject_directories(loader, dirname: str, tmp_path: Path) -> None:
    model_dir = tmp_path / dirname
    model_dir.mkdir()

    with pytest.raises(ModelError, match="not a file"):
        loader.load(ModelLoadRequest(source=model_dir))
