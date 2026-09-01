# AIHW-Bench

## AI Hardware Benchmark Suite

[![CI](https://github.com/shashi065/aihw-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/shashi065/aihw-bench/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/aihw-bench.svg)](https://pypi.org/project/aihw-bench/)
[![Python](https://img.shields.io/pypi/pyversions/aihw-bench.svg)](https://pypi.org/project/aihw-bench/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-4051b5.svg)](https://shashi065.github.io/aihw-bench/)

**AIHW-Bench** is a reproducible Python framework for benchmarking, profiling, comparing, and reporting AI workloads across CPUs, GPUs, embedded systems, simulator-backed environments, and extensible accelerator backends.

Measure the workload. Understand the hardware. Compare the results. Reproduce the experiment.

- Documentation: <https://shashi065.github.io/aihw-bench/>
- Repository: <https://github.com/shashi065/aihw-bench>
- Current stable release: **v2.0.0**

## Why AIHW-Bench?

| Need | AIHW-Bench provides |
| --- | --- |
| Reproducible measurements | Versioned configuration, immutable sessions, checksums, deterministic suite manifests, and report metadata. |
| Clear comparisons | Latency, throughput, resource metrics, session comparisons, reports, dashboard views, and a local benchmark analysis assistant. |
| Hardware-aware execution | Vendor-neutral capability reporting with explicit detection and runtime boundaries. |
| Extensibility | Replaceable model loaders, benchmark backends, metrics, reporters, visualizers, and plugins. |

## Architecture

```text
Configuration + workload
        │
        ▼
Benchmark service ──► backend + hardware inspection
        │                         │
        ▼                         ▼
immutable session ◄──────── measurements / observations
        │
        ├──► metrics + statistics
        ├──► JSON / CSV / Markdown / HTML reports
        ├──► static dashboard
        └──► local benchmark analysis assistant
```

## Install

```bash
python -m pip install aihw-bench
```

Optional runtime integrations are installed only when needed:

```bash
python -m pip install "aihw-bench[pytorch]"
python -m pip install "aihw-bench[onnx]"
python -m pip install "aihw-bench[all-backends]"
```

## Quick start

Run a deterministic reference benchmark and write a JSON report:

```bash
aihw-bench benchmark --backend reference --warmup 1 --iterations 10 --report json
```

Then inspect your environment and generated results:

```bash
aihw-bench doctor
aihw-bench report SESSION_ID --format html --format markdown
aihw-bench dashboard --storage-root .aihw-bench/sessions --output-dir dashboard
```

## Common workflows

### Compare two sessions

```bash
aihw-bench compare BASELINE_SESSION CANDIDATE_SESSION --output table
```

### Use the official reproducible suite

```bash
aihw-bench suite list
aihw-bench suite materialize --output-dir benchmarks
aihw-bench suite baselines --output-dir benchmarks
```

The suite ships deterministic synthetic inputs and reference fixtures. They validate benchmark plumbing and reproducibility; they are not universal real-device performance claims.

### Explain a result locally

```bash
aihw-bench assistant SESSION_ID --storage-root .aihw-bench/sessions
```

The built-in assistant is a deterministic, metric-grounded **local benchmark analysis assistant**. It is not an LLM and does not send benchmark data to an external service.

## Hardware support model

AIHW-Bench distinguishes four capability states:

| State | Meaning |
| --- | --- |
| **Detected** | Hardware or software was identified by a host/runtime probe. |
| **Reportable** | Its metadata can be stored and displayed. |
| **Runnable** | An installed backend can execute a benchmark for that target. |
| **Accelerated** | The selected workload/runtime actually uses the relevant acceleration path. |

This distinction matters: FPGA and RTL information can be detected or reported without implying synthesis, board programming, or vendor-tool execution. See the [hardware support guide](https://shashi065.github.io/aihw-bench/developer-guide/hardware-support/).

## Backends and runtimes

| Area | Built-in scope | Optional or plugin scope |
| --- | --- | --- |
| CPU | Reference and CPU benchmark backends | Runtime-specific optimization paths |
| GPU | CUDA, ROCm, and Intel GPU capability-aware target validation | Matching runtime/backend installation is required for execution and acceleration |
| Models | Metadata and loader contracts | PyTorch, ONNX Runtime, TensorFlow Lite, and third-party plugins |
| Embedded / specialized | Raspberry Pi, Jetson, Coral, FPGA placeholder, and RTL metadata/reporting | Board-specific, vendor, and simulator execution integrations |

## Reproducibility and reporting

Every benchmark session captures resolved configuration, hardware context, execution samples, metrics, diagnostics, and artifact checksums. Built-in reporters generate JSON, CSV, Markdown, and HTML; the static dashboard supports history browsing, filtering, comparison, and export.

- [Quick start](https://shashi065.github.io/aihw-bench/user-guide/quick-start/)
- [CLI reference](https://shashi065.github.io/aihw-bench/user-guide/cli/)
- [Official benchmark suite](https://shashi065.github.io/aihw-bench/benchmarks/official-suite/)
- [Dashboard](https://shashi065.github.io/aihw-bench/user-guide/dashboard/)
- [Assistant](https://shashi065.github.io/aihw-bench/user-guide/assistant/)
- [API reference](https://shashi065.github.io/aihw-bench/api/)

## Project status

AIHW-Bench v2.0.0 is feature-complete and maintained as a stable local benchmarking and reporting toolkit. Distributed remote execution, marketplace installation, real FPGA programming, and model-backed assistant providers remain extension areas rather than claims of the core package.

## Development

```bash
python -m pip install poetry
poetry install --with dev,docs
poetry run pytest
poetry run ruff check src tests scripts
poetry run black --check src tests scripts
poetry run mypy src
poetry run mkdocs build --strict
```

See the [contribution guide](CONTRIBUTING.md), [security policy](SECURITY.md), and [engineering documentation](https://shashi065.github.io/aihw-bench/engineering/).

## License

AIHW-Bench is licensed under the [Apache License 2.0](LICENSE).
