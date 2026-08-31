# Advanced Guide

This guide describes how the implemented components fit together for larger benchmark workflows.

## Configuration Precedence

Configuration is resolved in this order, from lowest to highest precedence:

1. Built-in defaults.
2. Configuration file values.
3. `AIHW_BENCH_` environment variables.
4. CLI overrides.

Nested environment variables use double underscores:

```bash
AIHW_BENCH_EXECUTION__ITERATIONS=20
AIHW_BENCH_BACKEND__DEVICE=gpu
```

Use the CLI to inspect the final resolved configuration before running a benchmark:

```bash
aihw-bench config --config examples/configs/reference-benchmark.yaml --output yaml
```

## Backend Selection

The backend registry selects a backend by configured backend name first, then by device support. Built-in backends include:

- `reference` for deterministic framework validation.
- `cpu` for CPU-oriented local execution metadata.
- `gpu` for CUDA-capable hosts when GPU hardware is available.

Backends validate configuration, hardware capability, precision, and workload compatibility before execution.

## Model Loading

The model registry supports PyTorch, ONNX Runtime, and TensorFlow Lite loader adapters. Optional runtime dependencies are imported only when a matching model is loaded, which keeps the base package usable in lightweight environments.

## Reporting And Visualization

Reports are generated from finalized sessions. The report service builds one report view and renders it through format-specific reporters. The visualization service can attach dashboard-ready chart components for latency, throughput, memory, timeline, hardware comparison, performance comparison, and roofline foundation views.

## Reproducible Runs

For reproducible automation:

- Keep configuration files under version control.
- Pin package versions in the execution environment.
- Store generated session JSON as the canonical run record.
- Preserve report artifacts and coverage output in CI.
- Prefer deterministic or fake backends for tests.

## Failure Policy

Expected failures raise typed AIHW-Bench errors with a message, cause, suggestion, and documentation link. CLI commands print those fields and return non-zero exit codes. Plugin failures are isolated as diagnostics unless strict mode is enabled.
