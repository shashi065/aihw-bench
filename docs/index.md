<div class="hero" markdown>

# AIHW-Bench

## AI Hardware Benchmark Suite

**Measure AI workloads. Understand the hardware. Compare the results. Reproduce the experiment.**

A reproducible Python framework for benchmarking, profiling, comparing, and reporting AI workloads across CPUs, GPUs, embedded systems, simulator-backed environments, and extensible accelerator backends.

<a class="md-button md-button--primary" href="user-guide/quick-start/">Get started</a>
<a class="md-button" href="user-guide/cli/">CLI reference</a>
<a class="md-button" href="developer-guide/architecture/">Architecture</a>

</div>

<div class="capability-grid" markdown>

<div class="capability-card" markdown>

### Reproducible experiments

Resolved configuration, deterministic suite manifests, immutable sessions, checksums, and portable reports make a measurement reviewable.

</div>

<div class="capability-card" markdown>

### Hardware-aware reporting

Capture CPU, GPU, embedded, accelerator, runtime, thermal, and power-policy context without overstating execution support.

</div>

<div class="capability-card" markdown>

### Compare with evidence

Inspect latency, throughput, resource metrics, diagnostics, session deltas, reports, and dashboard history.

</div>

<div class="capability-card" markdown>

### Designed to extend

Use backends, loaders, metrics, reporters, visualizers, and plugins to integrate supported runtimes and hardware.

</div>

</div>

## From workload to evidence

```text
Configuration + workload
        │
        ▼
Benchmark engine ──► backend + hardware inspection
        │
        ▼
Immutable benchmark session
        │
        ├──► metrics and statistics
        ├──► reports and export artifacts
        ├──► dashboard history and comparisons
        └──► local benchmark analysis assistant
```

## Start in minutes

```bash
python -m pip install aihw-bench
aihw-bench benchmark --backend reference --warmup 1 --iterations 10 --report json
```

Continue with the [Quick Start](user-guide/quick-start.md), explore the [CLI](user-guide/cli.md), or materialize the [official suite](benchmarks/official-suite.md).

## Hardware support, stated precisely

| Capability state | What it means |
| --- | --- |
| **Detected** | A host or runtime probe identified the hardware/software. |
| **Reportable** | AIHW-Bench can capture and display its metadata. |
| **Runnable** | An executable backend exists for the selected target. |
| **Accelerated** | The workload/runtime actually uses that acceleration path. |

Detection alone does not imply execution. For example, FPGA and RTL entries are reportable integration boundaries; the core package does not synthesize designs, program boards, or invoke vendor simulator binaries. Read the [hardware support guide](developer-guide/hardware-support.md) for the exact boundaries.

## Project status

<span class="status-pill">Stable v2.0.0</span>
<span class="status-pill">Python 3.12+</span>
<span class="status-pill">Local-first</span>

The official suite uses deterministic synthetic inputs and **reference fixtures / synthetic baselines**. Real-device results require a compatible workload/runtime and a documented hardware test environment. The built-in assistant is a deterministic, metric-grounded **local benchmark analysis assistant**—not an LLM service.

## Explore the documentation

| Start here | Build and extend | Operate and compare |
| --- | --- | --- |
| [Installation](user-guide/installation.md) | [Developer guide](developer-guide/architecture.md) | [Dashboard](user-guide/dashboard.md) |
| [Quick start](user-guide/quick-start.md) | [Plugin development](developer-guide/plugin-development.md) | [Reports](developer-guide/reporting.md) |
| [Official suite](benchmarks/official-suite.md) | [API reference](api/index.md) | [Enterprise foundations](enterprise.md) |

The full engineering record—including architecture, security, storage, testing, and release specifications—remains available in [Engineering](engineering/prd.md).
