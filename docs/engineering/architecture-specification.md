# Architecture Specification

## 1. Project Overview

### Vision

AIHW-Bench is a long-lived, vendor-neutral benchmarking framework for AI hardware and execution environments. It is designed to evaluate laptops, servers, GPUs, embedded AI devices, RTL simulators, FPGA platforms, ASIC prototypes, and future custom accelerators through one reproducible model.

### Mission

Provide accurate, extensible, reproducible, and developer-friendly AI hardware evaluation across research, product engineering, and open-source ecosystems.

### Goals

- Define one canonical benchmark lifecycle across all backends.
- Keep runtime, hardware, reporting, visualization, and storage implementations replaceable.
- Produce reproducible benchmark sessions with durable metadata.
- Support stable Python APIs, CLI workflows, plugin APIs, and machine-readable artifacts.
- Scale from local developer machines to distributed lab environments.

### Target Users

- Researchers publishing benchmark results.
- Hardware engineers validating silicon and simulator behavior.
- FPGA and ASIC teams comparing design revisions.
- ML engineers evaluating deployment targets.
- Embedded engineers measuring constrained devices.
- Compiler developers testing graph lowering and runtime optimization.
- Accelerator vendors building third-party plugins.

### Core Use Cases

- Benchmark a model on a CPU, GPU, embedded target, simulator, or accelerator.
- Profile memory, utilization, and execution timing.
- Compare two or more sessions for regressions or improvements.
- Generate HTML, Markdown, JSON, CSV, and future PDF reports.
- Publish reproducible benchmark artifacts.
- Extend the framework through third-party plugins.

### Supported Platforms

Initial support targets Python 3.12+ on Windows, Linux, and macOS. The architecture allows optional support for CUDA, ROCm, Metal, OpenVINO, ONNX Runtime execution providers, TensorFlow Lite delegates, RTL simulators, remote embedded devices, and vendor accelerator SDKs.

### Non-Goals

- AIHW-Bench is not a model training framework.
- AIHW-Bench is not a hosted benchmark database in its core package.
- AIHW-Bench does not bundle vendor SDKs or simulator binaries.
- AIHW-Bench does not execute untrusted plugin code in a security sandbox during the initial architecture.
- AIHW-Bench does not define benchmark claims without storing the configuration and environment metadata needed to reproduce them.

### Project Scope

In scope:

- Benchmark orchestration.
- Profiling orchestration.
- Metric computation.
- Session persistence.
- Report generation.
- Visualization data preparation.
- Plugin discovery and validation.
- CLI and Python API surfaces.
- Release, packaging, documentation, and testing standards.

Out of scope for the core package:

- Vendor-specific SDK redistribution.
- Cloud-hosted multi-tenant control planes.
- Private benchmark result certification.

### Success Metrics

- Reproducible sessions can be rerun from stored configuration.
- Core installation remains lightweight.
- Plugins can add backend support without modifying core modules.
- Public API changes are versioned and documented.
- Release automation produces installable packages and verified artifacts.
- Documentation is sufficient for an independent engineering team to implement or extend a subsystem.

## 2. High-Level Architecture

### Layered Architecture

```text
Presentation
  CLI, future dashboard, human output, machine output
Application
  Use cases, orchestration, configuration resolution, dependency injection
Domain
  Entities, value objects, policies, ports, result models
Infrastructure
  Runtime adapters, profilers, storage, reports, visualizations, plugins
Utilities
  Units, clocks, paths, serialization, logging, hashing
```

Dependencies point inward. Domain modules must not import presentation or infrastructure modules. Infrastructure implements domain ports. Presentation composes concrete dependencies but does not own business rules.

### Component Diagram

```text
User or Automation
  -> CLI or Python API
  -> Application Service
  -> Domain Policy and Ports
  -> Infrastructure Adapter
  -> Runtime, Device, Store, Reporter, or Plugin
```

### Module Relationships

- Presentation converts user input into application command objects.
- Application resolves configuration, selects ports, runs use cases, and returns result objects.
- Domain defines the types and rules that all implementations must respect.
- Infrastructure performs side effects and integrates with external systems.
- Utilities provide dependency-neutral helpers.

### Dependency Flow

Allowed flow:

```text
presentation -> application -> domain
presentation -> infrastructure -> application/domain
infrastructure -> domain
application -> domain
utilities -> standard library only or dependency-neutral libraries
```

Forbidden flow:

```text
domain -> application
domain -> infrastructure
domain -> presentation
application -> presentation
backend adapter -> another backend adapter
visualization -> benchmark execution service
```

### Subsystem Communication

Subsystems communicate through typed command, result, and port objects. They do not share hidden mutable state. Long-running operations expose progress events through application-level event streams so CLI, dashboard, and automation consumers can render progress independently.

### Data Flow

```text
Configuration Sources
  -> Resolved Configuration
  -> Workload and Backend Selection
  -> Benchmark Execution
  -> Raw Observations
  -> Metric Computation
  -> Session Store
  -> Reports, Visualizations, Exports, Comparisons
```

### Plugin Flow

```text
Installed Python Packages
  -> Entry Point Discovery
  -> Descriptor Validation
  -> Provider Registration
  -> Capability Resolution
  -> Use Case Execution
```

Plugin errors are collected as diagnostics. A failed plugin does not prevent unrelated built-in providers from loading.

### Benchmark Flow

```text
Load config
Validate workload
Inspect hardware
Prepare backend
Run warmup
Run measured iterations
Collect observations
Collect profiler samples
Compute statistics
Persist session
Generate artifacts
Release resources
```

### Report Generation Flow

```text
Session or Comparison
  -> Report Data Model
  -> Visualization Data
  -> Template or Structured Writer
  -> Artifact Store
```

Reports are post-processing operations and must not mutate canonical benchmark data.

### CLI Flow

```text
Command arguments
  -> CLI parser
  -> Configuration override object
  -> Application command
  -> Application result
  -> Rich output or machine-readable output
  -> Exit code
```

CLI output must remain separate from service behavior so Python API consumers receive the same domain results without terminal formatting.

## Architectural Invariants

- Benchmark sessions are immutable after finalization.
- Raw observations are retained before aggregation.
- Units are explicit on every metric.
- Optional runtime dependencies are isolated behind extras or plugins.
- Public extension contracts are versioned.
- All side effects occur through infrastructure adapters.
