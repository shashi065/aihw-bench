"""Hardware inspection and capability collection."""

from __future__ import annotations

import importlib
import logging
import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aihw_bench.domain.models import HardwareProfile
from aihw_bench.domain.ports import HardwareInspector

_DEVICE_TREE_MODELS = (Path("/proc/device-tree/model"), Path("/sys/firmware/devicetree/base/model"))


@dataclass(slots=True)
class SystemHardwareInspector(HardwareInspector):
    """Collect portable host, accelerator, embedded-target, and capability metadata.

    The inspector avoids vendor SDK requirements. Optional runtime probes are used only
    when their packages are already installed, and static probes are cached per instance.
    """

    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("aihw_bench.hardware"))
    _cached_profile: HardwareProfile | None = field(default=None, init=False, repr=False)

    def inspect(self) -> HardwareProfile:
        """Return a cached static profile with current thermal and power policy values."""
        if self._cached_profile is None:
            self._cached_profile = self._collect_profile()
        return self._cached_profile.model_copy(
            update={
                "thermal_policy": self._env_or_none("AIHW_BENCH_THERMAL_POLICY"),
                "power_policy": self._env_or_none("AIHW_BENCH_POWER_POLICY"),
            }
        )

    def _collect_profile(self) -> HardwareProfile:
        cpu = self._cpu_snapshot()
        memory = self._memory_snapshot()
        gpu = self._gpu_snapshot()
        accelerators = [*self._accelerators_snapshot(gpu), *self._fpga_snapshot()]
        embedded_target = self._embedded_snapshot()
        hardware = HardwareProfile(
            host_name=platform.node() or None,
            cpu=cpu,
            memory=memory,
            gpu=gpu,
            accelerators=accelerators,
            embedded_target=embedded_target,
            driver_versions=self._driver_versions(gpu),
            simulator=self._simulator_snapshot(),
        )
        self.logger.info("Collected hardware profile for %s", hardware.host_name or "unknown host")
        return hardware

    @staticmethod
    def _cpu_snapshot() -> dict[str, Any]:
        machine = platform.machine()
        processor = platform.processor() or machine or "unknown"
        cpuinfo = _read_text(Path("/proc/cpuinfo"))
        model_name = _cpuinfo_value(cpuinfo, "model name") or _cpuinfo_value(cpuinfo, "Hardware")
        vendor = _cpu_vendor(f"{processor} {model_name or ''} {machine}")
        return {
            "name": model_name or processor,
            "vendor": vendor,
            "architecture": machine,
            "cores": os.cpu_count(),
            "python": sys.version.split()[0],
            "features": _cpu_features(cpuinfo),
            "apple_silicon": vendor == "apple" and machine.lower() in {"arm64", "aarch64"},
        }

    @staticmethod
    def _memory_snapshot() -> dict[str, Any]:
        total = None
        try:
            sysconf_names = getattr(os, "sysconf_names", {})
            if (
                hasattr(os, "sysconf")
                and "SC_PAGE_SIZE" in sysconf_names
                and "SC_PHYS_PAGES" in sysconf_names
            ):
                total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        except (OSError, ValueError, AttributeError):
            total = None
        return {"total_bytes": total, "available": total is not None}

    @staticmethod
    def _gpu_snapshot() -> dict[str, Any]:
        try:
            torch = importlib.import_module("torch")
            cuda = getattr(torch, "cuda", None)
            if (
                cuda is None
                or not callable(getattr(cuda, "is_available", None))
                or not cuda.is_available()
            ):
                return _intel_gpu_snapshot()
            version = getattr(torch, "version", None)
            hip_version = getattr(version, "hip", None)
            backend = "rocm" if hip_version else "cuda"
            count = int(cuda.device_count()) if callable(getattr(cuda, "device_count", None)) else 0
            devices = [
                {
                    "index": index,
                    "name": (
                        cuda.get_device_name(index)
                        if callable(getattr(cuda, "get_device_name", None))
                        else f"{backend}:{index}"
                    ),
                    "vendor": "amd" if backend == "rocm" else "nvidia",
                    "capabilities": [backend],
                }
                for index in range(count)
            ]
            return {
                "available": bool(devices),
                "backend": backend,
                "runtime_version": hip_version or getattr(version, "cuda", None),
                "devices": devices,
            }
        except (ModuleNotFoundError, ImportError):
            return _intel_gpu_snapshot()
        except Exception:
            return {"available": False}

    @staticmethod
    def _accelerators_snapshot(gpu: dict[str, Any]) -> list[dict[str, Any]]:
        if not gpu.get("available"):
            return []
        return [
            {
                "kind": "gpu",
                "name": device.get("name"),
                "index": device.get("index"),
                "backend": gpu.get("backend"),
                "vendor": device.get("vendor"),
                "capabilities": device.get("capabilities", []),
            }
            for device in gpu.get("devices", [])
        ]

    @staticmethod
    def _fpga_snapshot() -> list[dict[str, Any]]:
        name = os.environ.get("AIHW_BENCH_FPGA_NAME")
        if not name:
            return []
        return [
            {
                "kind": "fpga",
                "name": name,
                "vendor": os.environ.get("AIHW_BENCH_FPGA_VENDOR", "unknown"),
                "capabilities": ["placeholder"],
                "available": False,
            }
        ]

    @staticmethod
    def _embedded_snapshot() -> dict[str, Any]:
        model = next((text for path in _DEVICE_TREE_MODELS if (text := _read_text(path))), "")
        lowered = model.lower()
        if "jetson" in lowered or "tegra" in lowered:
            return {"family": "jetson", "model": model, "capabilities": ["cuda", "embedded"]}
        if "raspberry pi" in lowered:
            return {"family": "raspberry-pi", "model": model, "capabilities": ["arm", "embedded"]}
        if "coral" in lowered or os.environ.get("AIHW_BENCH_CORAL_TPU"):
            return {
                "family": "coral",
                "model": model or "Coral TPU",
                "capabilities": ["edge-tpu", "embedded"],
            }
        return {}

    @staticmethod
    def _simulator_snapshot() -> dict[str, Any]:
        simulator = os.environ.get("AIHW_BENCH_RTL_SIMULATOR")
        if not simulator:
            return {}
        return {
            "name": simulator,
            "version": os.environ.get("AIHW_BENCH_RTL_SIMULATOR_VERSION"),
            "capabilities": ["rtl", "cycle-count", "waveform-artifacts"],
        }

    @staticmethod
    def _driver_versions(gpu: dict[str, Any]) -> dict[str, str]:
        backend = gpu.get("backend")
        runtime_version = gpu.get("runtime_version")
        if backend and runtime_version:
            return {str(backend): str(runtime_version)}
        if backend:
            return {str(backend): "available"}
        return {}

    @staticmethod
    def _env_or_none(name: str) -> str | None:
        value = os.environ.get(name)
        return value if value else None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip("\x00\n ")
    except OSError:
        return ""


def _cpuinfo_value(cpuinfo: str, key: str) -> str | None:
    prefix = f"{key}:"
    for line in cpuinfo.splitlines():
        if line.lower().startswith(prefix.lower()):
            return line.split(":", 1)[1].strip() or None
    return None


def _cpu_features(cpuinfo: str) -> list[str]:
    flags = _cpuinfo_value(cpuinfo, "flags") or _cpuinfo_value(cpuinfo, "Features") or ""
    relevant = {"avx", "avx2", "avx512f", "neon", "sve", "amx_tile"}
    return sorted(set(flags.lower().split()) & relevant)


def _cpu_vendor(description: str) -> str:
    lowered = description.lower()
    if "intel" in lowered:
        return "intel"
    if "amd" in lowered:
        return "amd"
    if "apple" in lowered or ("arm64" in lowered and platform.system() == "Darwin"):
        return "apple"
    return "unknown"


def _intel_gpu_snapshot() -> dict[str, Any]:
    devices: list[dict[str, Any]] = []
    for card in Path("/sys/class/drm").glob("card[0-9]*"):
        vendor = _read_text(card / "device" / "vendor")
        if vendor == "0x8086":
            devices.append(
                {
                    "index": len(devices),
                    "name": card.name,
                    "vendor": "intel",
                    "capabilities": ["intel-gpu", "oneapi"],
                }
            )
    if not devices:
        return {"available": False}
    return {"available": True, "backend": "intel-gpu", "devices": devices}
