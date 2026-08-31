# Architecture

The implementation follows Clean Architecture:

```text
presentation -> application -> domain <- infrastructure
```

The domain layer owns benchmark concepts and extension ports. Application services orchestrate use cases. Infrastructure implements concrete adapters. Presentation exposes the CLI.

Import boundaries are part of the project contract and should be preserved in review.

## Implemented Subsystems

- Core configuration, logging, errors, utilities, sessions, validation, and data models.
- Benchmark orchestration with scheduler, lifecycle tracking, timing engines, statistics, persistence, and report hooks.
- Model loading for PyTorch, ONNX Runtime, and TensorFlow Lite when optional runtimes are installed.
- Reference, CPU, and GPU backend support with hardware inspection and registry-based selection.
- Metrics for latency, throughput, memory, utilization, FLOPS estimates, summaries, and serialization.
- Report generation for JSON, CSV, Markdown, and HTML.
- Visualization specifications, dashboard components, and HTML, SVG, and PNG chart exports.
- Typer-based CLI commands for benchmark, profile, compare, report, export, config, doctor, completion, and version.
- Plugin discovery, registration, compatibility checks, dependency resolution, lifecycle, diagnostics, and configuration.
- Unit, integration, CLI, performance, and regression tests with coverage automation.
