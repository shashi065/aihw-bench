from __future__ import annotations

from types import SimpleNamespace

import pytest

from aihw_bench.domain.errors import BackendError
from aihw_bench.domain.models import Configuration, ExecutionPhase, HardwareProfile
from aihw_bench.infrastructure.backends import (
    BackendRegistryImpl,
    CPUBackend,
    FpgaPlaceholderBackend,
    GPUBackend,
    RtlSimulatorBackend,
    default_backend_registry,
)
from aihw_bench.infrastructure.hardware import SystemHardwareInspector

EXPECTED_GPU_COUNT = 2
EXPECTED_RTL_CYCLE_COUNT = 42


def test_cpu_backend_accepts_cpu_device() -> None:
    backend = CPUBackend()
    configuration = Configuration()

    backend.validate(configuration, HardwareProfile(), None)

    assert backend.supports_device("cpu")


def test_cpu_backend_rejects_unsupported_precision() -> None:
    backend = CPUBackend()
    configuration = Configuration(
        execution=Configuration().execution.model_copy(update={"precision": "bf16"})
    )

    with pytest.raises(BackendError, match="precision"):
        backend.validate(configuration, HardwareProfile(), None)


def test_gpu_backend_accepts_available_gpu_hardware() -> None:
    backend = GPUBackend()
    configuration = Configuration(
        backend=Configuration().backend.model_copy(update={"device": "cuda:0"})
    )
    hardware = HardwareProfile(
        gpu={
            "available": True,
            "backend": "cuda",
            "devices": [
                {"index": 0, "name": "Test GPU", "vendor": "nvidia", "capabilities": ["cuda"]}
            ],
        }
    )

    backend.validate(configuration, hardware, None)


def test_gpu_backend_rejects_missing_gpu_hardware() -> None:
    backend = GPUBackend()
    configuration = Configuration(
        backend=Configuration().backend.model_copy(update={"device": "cuda:0"})
    )

    with pytest.raises(BackendError, match="GPU hardware is not available"):
        backend.validate(configuration, HardwareProfile(), None)


def test_gpu_backend_rejects_unsupported_precision_before_execution() -> None:
    backend = GPUBackend()
    configuration = Configuration(
        backend=Configuration().backend.model_copy(update={"device": "cuda:0"}),
        execution=Configuration().execution.model_copy(update={"precision": "bf16"}),
    )
    hardware = HardwareProfile(gpu={"available": True})

    with pytest.raises(BackendError, match="precision"):
        backend.validate(configuration, hardware, None)


def test_backend_registry_selects_cpu_backend_for_default_configuration() -> None:
    registry = default_backend_registry()
    configuration = Configuration()

    backend = registry.select(configuration, HardwareProfile())

    assert backend.name == "cpu"


def test_backend_registry_rejects_unknown_backend_name() -> None:
    registry = BackendRegistryImpl()

    with pytest.raises(BackendError, match="not registered"):
        registry.resolve("missing")


def test_system_hardware_inspector_returns_a_profile() -> None:
    hardware = SystemHardwareInspector().inspect()

    assert hardware.cpu["name"]
    assert "total_bytes" in hardware.memory


def test_system_hardware_inspector_collects_gpu_when_torch_reports_cuda(monkeypatch) -> None:
    fake_cuda = SimpleNamespace(
        is_available=lambda: True,
        device_count=lambda: EXPECTED_GPU_COUNT,
        get_device_name=lambda index: f"GPU {index}",
    )
    fake_torch = SimpleNamespace(cuda=fake_cuda)

    def fake_import_module(name: str):
        if name == "torch":
            return fake_torch
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(
        "importlib.import_module",
        fake_import_module,
    )

    hardware = SystemHardwareInspector().inspect()

    assert hardware.gpu["available"] is True
    assert hardware.accelerators[0]["name"] == "GPU 0"
    assert hardware.driver_versions == {"cuda": "available"}


def test_system_hardware_inspector_handles_torch_without_cuda(monkeypatch) -> None:
    monkeypatch.setattr(
        "importlib.import_module",
        lambda name: (
            SimpleNamespace(cuda=None)
            if name == "torch"
            else (_ for _ in ()).throw(ModuleNotFoundError(name))
        ),
    )

    hardware = SystemHardwareInspector().inspect()

    assert hardware.gpu == {"available": False}
    assert hardware.accelerators == []


def test_system_hardware_inspector_reads_policy_environment(monkeypatch) -> None:
    monkeypatch.setenv("AIHW_BENCH_THERMAL_POLICY", "fixed-fan")
    monkeypatch.setenv("AIHW_BENCH_POWER_POLICY", "performance")

    hardware = SystemHardwareInspector().inspect()

    assert hardware.thermal_policy == "fixed-fan"
    assert hardware.power_policy == "performance"


def test_system_hardware_inspector_caches_static_probes_per_instance(monkeypatch) -> None:
    calls = 0
    fake_cuda = SimpleNamespace(is_available=lambda: False)
    fake_torch = SimpleNamespace(cuda=fake_cuda)

    def fake_import_module(name: str):
        nonlocal calls
        calls += 1
        assert name == "torch"
        return fake_torch

    monkeypatch.setattr("importlib.import_module", fake_import_module)
    inspector = SystemHardwareInspector()

    first = inspector.inspect()
    monkeypatch.setenv("AIHW_BENCH_THERMAL_POLICY", "quiet")
    second = inspector.inspect()

    assert calls == 1
    assert first.thermal_policy is None
    assert second.thermal_policy == "quiet"


@pytest.mark.parametrize(
    ("device", "gpu"),
    [
        (
            "rocm:0",
            {
                "available": True,
                "backend": "rocm",
                "devices": [{"vendor": "amd", "capabilities": ["rocm"]}],
            },
        ),
        (
            "intel-gpu:0",
            {
                "available": True,
                "backend": "intel-gpu",
                "devices": [{"vendor": "intel", "capabilities": ["intel-gpu"]}],
            },
        ),
    ],
)
def test_gpu_backend_accepts_matching_normalized_targets(
    device: str, gpu: dict[str, object]
) -> None:
    configuration = Configuration(
        backend=Configuration().backend.model_copy(update={"device": device})
    )
    GPUBackend().validate(configuration, HardwareProfile(gpu=gpu), None)


@pytest.mark.parametrize(
    ("device", "gpu"),
    [
        ("cuda:0", {"available": True, "devices": [{"vendor": "nvidia", "capabilities": []}]}),
        ("cuda:0", {"available": True, "devices": [{"vendor": "amd", "capabilities": ["rocm"]}]}),
        (
            "rocm:0",
            {"available": True, "devices": [{"vendor": "intel", "capabilities": ["intel-gpu"]}]},
        ),
        (
            "intel-gpu:0",
            {"available": True, "devices": [{"vendor": "unknown", "capabilities": []}]},
        ),
    ],
)
def test_gpu_backend_rejects_mismatched_or_unavailable_runtime(
    device: str, gpu: dict[str, object]
) -> None:
    configuration = Configuration(
        backend=Configuration().backend.model_copy(update={"device": device})
    )
    with pytest.raises(BackendError, match="Requested GPU target is not available"):
        GPUBackend().validate(configuration, HardwareProfile(gpu=gpu), None)


def test_rtl_backend_preserves_normalized_simulator_observations() -> None:
    backend = RtlSimulatorBackend()
    configuration = Configuration(
        backend=Configuration().backend.model_copy(
            update={
                "name": "rtl",
                "device": "rtl",
                "options": {"rtl_observations": {"cycle_count": 42}},
            }
        )
    )
    assert backend.prepare(configuration, HardwareProfile(), None)["backend"] == "rtl"
    assert (
        backend.execute(ExecutionPhase.MEASUREMENT, 0, configuration, HardwareProfile(), None)[
            "cycle_count"
        ]
        == EXPECTED_RTL_CYCLE_COUNT
    )


def test_fpga_placeholder_requires_board_plugin() -> None:
    backend = FpgaPlaceholderBackend()
    configuration = Configuration(
        backend=Configuration().backend.model_copy(update={"name": "fpga", "device": "fpga"})
    )
    with pytest.raises(BackendError, match="board-specific plugin"):
        backend.prepare(configuration, HardwareProfile(), None)


def test_hardware_profile_capability_report_normalizes_platform_data() -> None:
    hardware = HardwareProfile(
        cpu={
            "vendor": "apple",
            "architecture": "arm64",
            "features": ["neon"],
            "apple_silicon": True,
        },
        gpu={"available": True, "backend": "cuda", "devices": [{"capabilities": ["cuda"]}]},
        embedded_target={"family": "jetson"},
    )
    report = hardware.capability_report()
    assert report["cpu"]["apple_silicon"] is True
    assert report["gpu"]["capabilities"] == ["cuda"]
    assert report["embedded"]["family"] == "jetson"
