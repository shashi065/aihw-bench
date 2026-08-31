from __future__ import annotations

from pathlib import Path

from aihw_bench.application import BenchmarkRequest, BenchmarkService, ScriptedTimingEngine
from aihw_bench.domain.model_support import LoadedModel
from aihw_bench.domain.models import (
    Configuration,
    ExecutionConfig,
    ModelMetadata,
    SessionStatus,
    WorkloadConfig,
)
from aihw_bench.infrastructure.backends import ReferenceBenchmarkBackend


class FakeModelCatalog:
    def load_workload(self, workload: WorkloadConfig) -> LoadedModel:
        metadata = ModelMetadata(
            model_id=workload.name or "configured-model",
            name=workload.name or "configured-model",
            format="onnx",
            framework="onnxruntime",
            source=workload.source,
            input_shapes=dict(workload.input_shapes),
            metadata=dict(workload.metadata),
        )
        return LoadedModel(
            source=Path(workload.source or "model.onnx"), loader_name="fake", metadata=metadata
        )


def test_benchmark_service_resolves_workload_from_configuration(tmp_path) -> None:
    model_file = tmp_path / "model.onnx"
    model_file.write_bytes(b"fake model file")

    service = BenchmarkService(
        ReferenceBenchmarkBackend(),
        model_catalog=FakeModelCatalog(),
        timing_engine=ScriptedTimingEngine([0.05]),
    )
    request = BenchmarkRequest(
        session_id="model-session",
        configuration=Configuration(
            workload=WorkloadConfig(source=str(model_file), name="demo-model"),
            execution=ExecutionConfig(warmup_iterations=0, iterations=1),
        ),
    )

    outcome = service.run(request)

    assert outcome.session.status is SessionStatus.COMPLETED
    assert outcome.session.workload is not None
    assert outcome.session.workload.framework == "onnxruntime"
    assert outcome.session.workload.model_id == "demo-model"
