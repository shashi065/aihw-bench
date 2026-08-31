from __future__ import annotations

from aihw_bench.application import BenchmarkRequest, BenchmarkService, ScriptedTimingEngine
from aihw_bench.domain.models import Configuration, ExecutionConfig, HardwareProfile, SessionStatus
from aihw_bench.infrastructure.backends import default_backend_registry


class StaticHardwareInspector:
    def inspect(self) -> HardwareProfile:
        return HardwareProfile(
            host_name="test-host",
            cpu={"name": "test-cpu"},
            gpu={"available": False},
        )


class StaticGpuHardwareInspector:
    def inspect(self) -> HardwareProfile:
        return HardwareProfile(
            host_name="gpu-test-host",
            cpu={"name": "test-cpu"},
            gpu={
                "available": True,
                "backend": "cuda",
                "devices": [
                    {"index": 0, "name": "Test GPU", "vendor": "nvidia", "capabilities": ["cuda"]}
                ],
            },
        )


def test_benchmark_service_selects_backend_from_registry() -> None:
    service = BenchmarkService(
        backend=None,
        backend_registry=default_backend_registry(),
        hardware_inspector=StaticHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.01]),
    )
    request = BenchmarkRequest(
        session_id="backend-session",
        configuration=Configuration(
            backend=Configuration().backend.model_copy(update={"name": "cpu", "device": "cpu"}),
            execution=ExecutionConfig(warmup_iterations=0, iterations=1),
        ),
    )

    outcome = service.run(request)

    assert outcome.session.status is SessionStatus.COMPLETED
    assert outcome.session.backend["name"] == "cpu"
    assert outcome.session.hardware.host_name == "test-host"


def test_benchmark_service_selects_gpu_backend_from_registry() -> None:
    service = BenchmarkService(
        backend=None,
        backend_registry=default_backend_registry(),
        hardware_inspector=StaticGpuHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.01]),
    )
    request = BenchmarkRequest(
        session_id="gpu-backend-session",
        configuration=Configuration(
            backend=Configuration().backend.model_copy(update={"name": "gpu", "device": "cuda:0"}),
            execution=ExecutionConfig(warmup_iterations=0, iterations=1),
        ),
    )

    outcome = service.run(request)

    assert outcome.session.status is SessionStatus.COMPLETED
    assert outcome.session.backend["name"] == "gpu"
    assert outcome.session.hardware.host_name == "gpu-test-host"
