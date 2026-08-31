# Backend Support

Milestone 4 adds the initial hardware/backend layer used by the benchmark engine.

## Built-in Backends

- CPU backend for CPU-targeted execution.
- GPU backend for GPU/CUDA-targeted execution.
- Reference backend retained for deterministic validation tests.

## Hardware Inspection

`SystemHardwareInspector` collects a portable host snapshot using standard library probes and optional GPU hints when a compatible runtime is present.

## Backend Selection

`BackendRegistryImpl` resolves backends by name when available and otherwise selects a backend that supports the requested device. The benchmark service can use an injected registry and hardware inspector when a direct backend instance is not supplied.

## Validation

Backends validate device compatibility and execution precision before benchmark work begins. GPU validation also requires an inspected hardware profile with an available accelerator. Structured errors include the cause, a suggested fix, and a documentation link.

The built-in CPU and GPU backends currently advertise `fp32`, `fp16`, and `int8`. Requests for unsupported precision modes are rejected during backend selection or preparation, before warmup and measured iterations can run.

## Hardware Data

The hardware profile attached to each benchmark session records host, platform, CPU, memory, GPU, accelerator, driver, thermal, and power-policy fields. The standard inspector uses portable operating-system probes and optional runtime checks when packages such as PyTorch are installed.

## Public API

```python
from aihw_bench.infrastructure.backends import default_backend_registry
from aihw_bench.infrastructure.hardware import SystemHardwareInspector

registry = default_backend_registry()
hardware = SystemHardwareInspector().inspect()
backend = registry.select(configuration, hardware)
```
