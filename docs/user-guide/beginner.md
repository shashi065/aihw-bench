# Beginner Guide

AIHW-Bench runs repeatable benchmark sessions and stores the result as immutable session records. A session captures the resolved configuration, hardware summary, workload metadata, execution runs, metrics, reports, diagnostics, and generated artifacts.

## What You Can Do

- Run a benchmark from a YAML or JSON configuration.
- Load supported model formats through model loaders.
- Select CPU or GPU execution backends.
- Collect latency, throughput, memory, utilization, and estimated FLOPS metrics.
- Generate JSON, CSV, Markdown, and HTML reports.
- Export chart artifacts for dashboards and reports.
- Extend the system through plugins.

## Core Concepts

| Concept | Meaning |
| --- | --- |
| Configuration | The merged defaults, file settings, environment variables, and CLI overrides for a run. |
| Backend | The execution adapter responsible for validating, preparing, running, and cleaning up work. |
| Workload | The model or configured workload metadata being benchmarked. |
| Session | The durable record of one benchmark run. |
| Metric | A measured, derived, estimated, metadata, or unavailable value attached to a session. |
| Report | A rendered view of a finalized session. |
| Plugin | An installed package that contributes hardware, models, reports, visualizations, metrics, CLI commands, or exporters. |

## Minimal Workflow

1. Install the package in a Python 3.12+ environment.
2. Run `aihw-bench doctor` to validate local dependencies.
3. Create or reuse a benchmark configuration.
4. Run `aihw-bench benchmark`.
5. Inspect the generated session and reports.

```bash
aihw-bench doctor
aihw-bench benchmark --config examples/configs/reference-benchmark.yaml
aihw-bench report demo-session --format markdown --format html
```

The built-in reference backend is deterministic and is useful for smoke tests, documentation examples, and CI validation.

## Where To Go Next

- Use [Quick Start](quick-start.md) for a compact API and CLI walkthrough.
- Use [First Benchmark](../tutorials/first-benchmark.md) for a step-by-step session.
- Use [Advanced Guide](advanced.md) when combining backends, model loaders, reports, and plugins.
