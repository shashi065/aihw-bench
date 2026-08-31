# API Specification

## Public Package Layout

The stable Python API will be exposed from `aihw_bench` and documented subpackages. Internal modules may use leading underscores and are not covered by semantic versioning guarantees.

## Core Data Models

### BenchmarkConfig

Fields:

- `workload`: workload reference and input shape metadata.
- `backend`: backend identifier and backend-specific options.
- `device`: target device selector.
- `run`: warmup count, iteration count, timeout, retry policy, precision, and batch size.
- `metrics`: enabled metrics and thresholds.
- `reports`: requested report formats and output directory.
- `tags`: user-defined metadata for comparison and filtering.

### BenchmarkSession

Fields:

- `session_id`
- `created_at`
- `config`
- `system_info`
- `device_info`
- `runs`
- `metrics`
- `artifacts`

### BenchmarkRun

Fields:

- `run_id`
- `status`
- `started_at`
- `completed_at`
- `duration`
- `observations`
- `profiler_samples`
- `error`

### Metric

Fields:

- `name`
- `value`
- `unit`
- `source`
- `description`
- `assumptions`

## Domain Ports

### BenchmarkBackend

Responsibilities:

- Declare backend name, version, supported workload types, supported devices, and precision modes.
- Validate that a workload can execute.
- Prepare runtime resources outside measured regions.
- Execute warmup and measured iterations.
- Release backend resources.

### Profiler

Responsibilities:

- Declare profiler capabilities.
- Start and stop sampling around configured scopes.
- Return profiler samples with units and timestamps.

### MetricProvider

Responsibilities:

- Compute one or more metrics from benchmark sessions.
- Declare required observations and profiler samples.
- Return deterministic metric objects.

### Reporter

Responsibilities:

- Generate one report artifact from a benchmark session or comparison result.
- Declare supported output format.
- Preserve metric units and metadata.

### SessionStore

Responsibilities:

- Create immutable session records.
- Load sessions by identifier or path.
- List sessions by filters.
- Store generated artifacts.

### HardwareInspector

Responsibilities:

- Inspect host hardware and available accelerator metadata.
- Return a structured hardware profile.

### BackendRegistry

Responsibilities:

- Register backends.
- Resolve backends by name.
- Select a backend for a configuration and hardware profile.
- Validate backend compatibility before execution.

### ModelLoader

Responsibilities:

- Declare supported file extensions and framework name.
- Load a supported model source.
- Validate compatibility and extract metadata.

### ModelLoaderCatalog

Responsibilities:

- Resolve the correct loader for a source path or configured workload.
- Load model metadata through a registered loader.
- Support future format adapters without changing application code.

## Application Services

- `BenchmarkService`
- `ProfileService`
- `ComparisonService`
- `ReportService`
- `ExportService`
- `DoctorService`

Each service accepts validated command objects and returns typed result objects. Services do not print to stdout or import CLI frameworks.

## Compatibility Policy

Before `1.0.0`, public APIs may change between minor versions with changelog entries. Starting at `1.0.0`, breaking public API changes require a major version increment.
