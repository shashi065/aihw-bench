from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from aihw_bench.domain.model_support import LoadedModel, ModelLoader, ModelLoadRequest
from aihw_bench.domain.models import (
    Configuration,
    ExecutionPhase,
    HardwareProfile,
    ModelMetadata,
)
from aihw_bench.domain.ports import BenchmarkBackend, HardwareInspector


class FakeBackend(BenchmarkBackend):
    """Deterministic backend for tests that need controlled behavior."""

    name = "fake"
    version = "0.1.0"
    supported_devices = ("cpu", "cuda:0")
    supported_precisions = ("fp32", "fp16", "int8")

    def __init__(
        self,
        *,
        fail_on: set[tuple[ExecutionPhase, int, int]] | None = None,
        prepare_error: Exception | None = None,
        cleanup_error: Exception | None = None,
    ) -> None:
        self.fail_on = fail_on or set()
        self.prepare_error = prepare_error
        self.cleanup_error = cleanup_error
        self.calls: list[dict[str, Any]] = []
        self.attempts: dict[tuple[ExecutionPhase, int], int] = {}

    def supports_device(self, device: str) -> bool:
        return device in self.supported_devices

    def validate(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> None:
        self.calls.append({"operation": "validate", "device": configuration.backend.device})

    def prepare(
        self,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        self.calls.append({"operation": "prepare"})
        if self.prepare_error is not None:
            raise self.prepare_error
        return {"prepared": True}

    def execute(
        self,
        phase: ExecutionPhase,
        iteration: int,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
    ) -> Mapping[str, Any]:
        key = (phase, iteration)
        attempt = self.attempts.get(key, 0)
        self.attempts[key] = attempt + 1
        self.calls.append(
            {
                "operation": "execute",
                "phase": phase.value,
                "iteration": iteration,
                "attempt": attempt,
            }
        )
        if (phase, iteration, attempt) in self.fail_on:
            raise RuntimeError(f"planned failure {phase.value} {iteration} {attempt}")
        return {
            "memory_peak_bytes": 1024 + iteration,
            "cpu_utilization_percent": 40.0 + iteration,
        }

    def cleanup(self) -> None:
        self.calls.append({"operation": "cleanup"})
        if self.cleanup_error is not None:
            raise self.cleanup_error


class FakeHardwareInspector(HardwareInspector):
    """Test hardware inspector with deterministic output."""

    def inspect(self) -> HardwareProfile:
        return HardwareProfile(
            host_name="test-host",
            cpu={"name": "test-cpu", "cores": 8},
            memory={"total_bytes": 8192, "available": True},
        )


class FakeModelLoader(ModelLoader):
    """Simple model loader used by registry and benchmark tests."""

    name = "fake-loader"
    supported_extensions = frozenset({".fake"})

    def can_load(self, source: Path) -> bool:
        return source.suffix == ".fake"

    def load(self, request: ModelLoadRequest) -> LoadedModel:
        return LoadedModel(
            source=request.source,
            loader_name=self.name,
            metadata=ModelMetadata(
                model_id=request.name or request.source.stem,
                name=request.name or request.source.stem,
                format="fake",
                framework="fake-loader",
                source=str(request.source),
                input_shapes=dict(request.input_shapes),
                metadata=dict(request.metadata),
            ),
            handle={"source": str(request.source)},
        )


@pytest.fixture
def fake_backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def fake_hardware() -> HardwareProfile:
    return FakeHardwareInspector().inspect()


@pytest.fixture
def fake_model_file(tmp_path: Path) -> Path:
    model = tmp_path / "model.fake"
    model.write_bytes(b"fake model")
    return model
