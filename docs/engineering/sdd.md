# Software Design Document

Document status: Baseline  
Product: AI Hardware Benchmark Suite (`aihw-bench`)  
Design authority: Project Constitution, PRD, SRS, Architecture Specification

## 1. System Architecture

### 1.1 Layered Architecture

AIHW-Bench follows Clean Architecture. Dependencies point inward toward domain contracts.

```text
Presentation Layer
  CLI, future dashboard, shell completion, human and machine output
Application Layer
  Use cases, orchestration, dependency injection, progress events
Domain Layer
  Entities, value objects, policies, interfaces, invariants
Infrastructure Layer
  Backends, profilers, reports, visualizations, storage, plugins, packaging integrations
Utilities
  Clocks, units, paths, hashing, serialization, logging helpers
```

The domain layer is the stable center of the system. Infrastructure implementations can be replaced without changing business rules. Presentation code renders results but does not own benchmark behavior.

### 1.2 Component Architecture

```text
CLI or Python API
  -> Configuration Manager
  -> Application Service
  -> Provider Registry
  -> Benchmark Engine
  -> Backend, Profiler, Hardware Inspector, Model Loader
  -> Metrics Engine
  -> Session Manager
  -> Reporting, Visualization, Export
```

Each component communicates through typed commands, results, domain entities, and port interfaces. Components do not share hidden global state.

### 1.3 Package Architecture

Target package families:

- `aihw_bench.domain`: entities, value objects, policies, ports, domain errors.
- `aihw_bench.application`: use-case services and command/result objects.
- `aihw_bench.infrastructure`: adapters for configuration, storage, profiling, hardware, backends, reporting, visualization, plugins, package metadata.
- `aihw_bench.presentation`: CLI and future dashboard entry points.
- `aihw_bench.utils`: dependency-neutral helpers.

### 1.4 Dependency Graph

Allowed dependencies:

```text
presentation -> application
presentation -> infrastructure composition
application -> domain
application -> utils
infrastructure -> domain
infrastructure -> application command/result models only when necessary
infrastructure -> utils
domain -> standard library and approved model libraries
utils -> standard library or dependency-neutral libraries
```

Forbidden dependencies:

```text
domain -> application
domain -> infrastructure
domain -> presentation
application -> presentation
backend adapter -> unrelated backend adapter
visualization -> benchmark execution service
report generation -> benchmark mutation
```

### 1.5 Execution Flow

1. User invokes CLI or Python API.
2. Presentation builds a command object.
3. Configuration manager resolves effective configuration.
4. Application service validates use-case intent.
5. Provider registry resolves backends, profilers, metrics, reporters, visualizers, exporters, and storage.
6. Benchmark engine runs lifecycle.
7. Metrics engine aggregates observations.
8. Session manager persists immutable data.
9. Reporting/export systems create artifacts.
10. Presentation renders result and exit code.

### 1.6 Plugin Flow

1. Discover Python entry points in `aihw_bench.plugins`.
2. Import plugin descriptor in controlled loader context.
3. Validate descriptor schema and API version.
4. Validate provider names and capability metadata.
5. Register providers in registry.
6. Expose diagnostics through `doctor`.
7. Resolve providers by requested backend, metric, report, visualization, exporter, or CLI command.

### 1.7 CLI Flow

```text
arguments -> Typer parser -> override object -> resolved config -> service command -> service result -> renderer -> exit code
```

The CLI shall support Rich human output and structured machine output. CLI rendering must be separate from application behavior.

### 1.8 Reporting Flow

```text
session/comparison -> report view model -> visualization specs -> template or writer -> artifact manifest
```

Reports are post-processing artifacts. They never mutate canonical benchmark session data.

### 1.9 Visualization Flow

```text
session metrics/profiles -> normalized chart data -> chart spec -> embedded report artifact or dashboard payload
```

Visualization providers do not execute workloads and do not inspect live backend state.

### 1.10 Benchmark Lifecycle

```text
created -> configured -> providers-resolved -> prepared -> warming -> measuring -> aggregating -> persisted -> reporting -> finalized
```

Failure states:

- `failed_configuration`
- `failed_validation`
- `failed_backend`
- `failed_runtime`
- `failed_storage`
- `partial`
- `cancelled`

## 2. Subsystem Design

### 2.1 Benchmark Engine

Responsibilities:

- Own benchmark lifecycle orchestration.
- Coordinate backend preparation, warmup, measured execution, profiler scopes, metric aggregation, persistence, and cleanup.
- Preserve failed and partial run metadata.

Public interfaces:

- Benchmark service command/result.
- Benchmark backend port.
- Progress event stream.

Internal components:

- Execution planner.
- Lifecycle state machine.
- Warmup runner.
- Measurement runner.
- Cleanup coordinator.
- Failure classifier.

Dependencies:

- Configuration manager.
- Provider registry.
- Backend provider.
- Profiler providers.
- Metrics engine.
- Session manager.

Design patterns:

- Strategy for backend execution.
- Template Method for lifecycle phases.
- Observer for progress events.
- Dependency Injection for testability.

Future extension points:

- Parallel execution scheduler.
- Remote hardware lab runner.
- Distributed benchmark campaigns.

### 2.2 Profiler

Responsibilities:

- Collect timing, memory, CPU, GPU, accelerator, simulator, power, and thermal samples.
- Attach samples to benchmark scopes.
- Degrade gracefully when optional profilers are unavailable.

Public interfaces:

- `Profiler` provider contract.
- Profile sample model.
- Profile summary model.

Internal components:

- Scope manager.
- Sampler.
- Sample normalizer.
- Profiler diagnostics collector.

Dependencies:

- Benchmark lifecycle events.
- Hardware metadata.
- Optional platform or vendor APIs.

Design patterns:

- Context Manager for profiling scopes.
- Adapter for platform profilers.
- Null Object for disabled profilers.

Future extension points:

- Vendor profiler import.
- Trace event output.
- Energy measurement.

### 2.3 Metrics Engine

Responsibilities:

- Compute primary and derived metrics.
- Preserve units, assumptions, source, and comparison direction.
- Support plugin metric providers.

Public interfaces:

- `MetricProvider` contract.
- Metric registry.
- Metric computation result.

Internal components:

- Aggregator.
- Unit normalizer.
- Percentile calculator.
- Derived metric estimator.
- Missing metric classifier.

Dependencies:

- Benchmark observations.
- Profile samples.
- Model metadata.
- Hardware metadata.

Design patterns:

- Strategy for metric providers.
- Pipeline for metric computation stages.
- Value Object for unit-bearing quantities.

Future extension points:

- Confidence intervals.
- Energy efficiency metrics.
- Statistical validation plugins.

### 2.4 Hardware Layer

Responsibilities:

- Represent host and target hardware.
- Discover device capabilities.
- Support CPUs, GPUs, embedded devices, simulators, FPGA boards, ASIC prototypes, and custom accelerators.

Public interfaces:

- `HardwareInspector`.
- `DeviceSelector`.
- Hardware profile model.

Internal components:

- Host inspector.
- Target inspector.
- Capability resolver.
- Device metadata normalizer.

Dependencies:

- Platform APIs.
- Backend providers.
- Optional vendor tooling.

Design patterns:

- Adapter for hardware-specific inspection.
- Capability Object for device features.

Future extension points:

- Remote target inventory.
- Hardware lab scheduling.
- Power and thermal inspectors.

### 2.5 Model Layer

Responsibilities:

- Represent workloads and model metadata independently from execution runtimes.
- Validate workload/backend compatibility.
- Support model formats and custom workload types.

Public interfaces:

- `ModelLoader`.
- `Workload`.
- `ModelMetadata`.

Internal components:

- Format detector.
- Metadata extractor.
- Input specification resolver.
- Runtime compatibility checker.

Dependencies:

- Backend capabilities.
- Optional model runtime libraries.

Design patterns:

- Factory for workload loading.
- Adapter for runtime-specific model formats.

Future extension points:

- Compiler IR loaders.
- Synthetic workload generators.
- Dataset-aware workload specs.

### 2.6 Visualization Engine

Responsibilities:

- Convert session and comparison data into chart specifications.
- Support timeline, roofline, latency distribution, memory, scaling, comparison, and utilization visualizations.

Public interfaces:

- `Visualizer`.
- Chart specification model.
- Visualization registry.

Internal components:

- Chart data normalizer.
- Axis policy.
- Downsampler.
- Theme adapter.

Dependencies:

- Metrics, profiles, and report view models.
- Plotly or future chart renderers.

Design patterns:

- Strategy for chart providers.
- Builder for chart specifications.

Future extension points:

- Live dashboard charts.
- Large-session progressive rendering.

### 2.7 Reporting Engine

Responsibilities:

- Generate reports from sessions and comparisons.
- Support HTML, Markdown, JSON, CSV, future PDF, and interactive reports.
- Produce recommendations without overclaiming.

Public interfaces:

- `Reporter`.
- `ReportRequest`.
- `ReportArtifact`.

Internal components:

- Report view model builder.
- Template renderer.
- Structured writer.
- Recommendation engine.
- Artifact manifest writer.

Dependencies:

- Session manager.
- Visualization engine.
- Export engine.

Design patterns:

- Strategy for report formats.
- Presenter/View Model separation.

Future extension points:

- PDF renderer.
- Static dashboard bundle.
- Hosted report publishing.

### 2.8 Plugin Manager

Responsibilities:

- Discover, validate, register, and diagnose plugins.
- Support extension providers for hardware, metrics, reports, visualizations, models, CLI commands, exporters, and integrations.

Public interfaces:

- Plugin descriptor.
- Provider registry.
- Plugin diagnostics.

Internal components:

- Entry point scanner.
- Descriptor validator.
- Compatibility checker.
- Provider registry.

Dependencies:

- Python packaging metadata.
- Domain provider contracts.

Design patterns:

- Registry.
- Adapter.
- Fail-soft diagnostics.

Future extension points:

- Signed plugin manifests.
- Out-of-process plugin execution.
- Plugin marketplace metadata.

### 2.9 Configuration Manager

Responsibilities:

- Resolve CLI, environment, YAML, JSON, and default configuration.
- Support profiles, inheritance, overrides, validation, and source explanation.

Public interfaces:

- Configuration loader.
- Resolved configuration model.
- Configuration diagnostics.

Internal components:

- File reader.
- Environment parser.
- Merge engine.
- Profile resolver.
- Schema validator.

Dependencies:

- Pydantic settings.
- Safe path utilities.
- YAML/JSON readers.

Design patterns:

- Chain of Responsibility for source precedence.
- Builder for resolved configuration.

Future extension points:

- Remote configuration.
- Signed configuration bundles.
- Secret reference resolution.

### 2.10 Session Manager

Responsibilities:

- Persist immutable sessions and artifacts.
- Load, list, compare, and export sessions.
- Protect canonical data from mutation.

Public interfaces:

- `SessionStore`.
- Session manifest.
- Artifact registry.

Internal components:

- Filesystem store.
- Atomic writer.
- Schema reader.
- Migration coordinator.
- Artifact index.

Dependencies:

- Serialization utilities.
- Safe path resolver.

Design patterns:

- Repository.
- Unit of Work for session finalization.

Future extension points:

- SQLite store.
- PostgreSQL store.
- Object storage store.

### 2.11 Logging System

Responsibilities:

- Provide structured diagnostics for users and maintainers.
- Avoid leaking secrets.
- Support verbose and debug modes.

Public interfaces:

- Logging configuration.
- Diagnostic records.

Internal components:

- Log formatter.
- Secret redactor.
- Context enricher.

Dependencies:

- Standard logging.
- CLI verbosity configuration.

Design patterns:

- Decorator for diagnostic context.
- Filter for secret redaction.

Future extension points:

- OpenTelemetry tracing.
- JSON logs.

### 2.12 Package Manager

Responsibilities:

- Define package metadata.
- Support optional extras.
- Preserve lightweight core installation.

Public interfaces:

- Package metadata.
- Entry points.
- Optional dependency groups.

Internal components:

- Build configuration.
- Release artifact configuration.

Dependencies:

- PEP 517/518/621 build system.

Design patterns:

- Optional Adapter dependencies.

Future extension points:

- Native package metadata.
- Plugin package templates.

### 2.13 Documentation System

Responsibilities:

- Build user, developer, architecture, API, CLI, plugin, and release documentation.
- Enforce strict docs builds.

Public interfaces:

- MkDocs site.
- API reference.
- CLI reference.

Internal components:

- Navigation.
- Markdown source pages.
- Generated API docs.

Dependencies:

- MkDocs Material.
- mkdocstrings.

Design patterns:

- Documentation as product artifact.

Future extension points:

- Versioned docs.
- Tutorial gallery.

### 2.14 Release System

Responsibilities:

- Automate tag-driven releases.
- Build distributions, docs, SBOM, checksums, release notes, Docker images, and downstream metadata.
- Verify install on Windows, Linux, and macOS.

Public interfaces:

- Git tags.
- GitHub Actions workflows.
- Release artifacts.

Internal components:

- Version validator.
- Quality gates.
- Artifact builder.
- Publisher.
- Install verifier.

Dependencies:

- GitHub Actions.
- PyPI/TestPyPI trusted publishing.
- Container registry credentials.

Design patterns:

- Pipeline.
- Gatekeeper.

Future extension points:

- Signed provenance.
- Winget, Chocolatey, Snapcraft, AUR, and Nix automation.

## 3. Class Design

The following classes describe intended design contracts. Exact implementation may split classes into smaller units when doing so preserves responsibilities.

### 3.1 `BenchmarkSession`

Purpose: Immutable top-level benchmark record.

Attributes:

- `session_id`
- `schema_version`
- `created_at`
- `completed_at`
- `status`
- `configuration`
- `hardware_profile`
- `model_metadata`
- `results`
- `metrics`
- `profiles`
- `artifacts`
- `diagnostics`

Methods:

- `finalize(status)`
- `add_artifact(artifact)`
- `to_dict()`
- `from_dict(data)`

Relationships:

- Owns benchmark results, metrics, profiles, artifacts, and diagnostics.
- References resolved configuration and plugin metadata.

Lifecycle:

- Created as pending.
- Updated during execution.
- Finalized as immutable.

Thread safety:

- Mutable only within one session coordinator before finalization.
- Finalized instances are read-only.

Serialization:

- JSON/YAML serializable with schema version.

Validation:

- Requires session ID, schema version, timestamps, status, and resolved configuration.

Error handling:

- Invalid mutation after finalization raises a session state error.

### 3.2 `BenchmarkResult`

Purpose: Aggregate result for one workload/backend/device configuration.

Attributes:

- `result_id`
- `session_id`
- `status`
- `execution_results`
- `primary_metrics`
- `secondary_metrics`
- `statistics`
- `comparison_keys`
- `error`

Methods:

- `is_successful()`
- `primary_metric(name)`
- `to_summary()`

Relationships:

- Belongs to one session.
- Aggregates execution results and metrics.

Lifecycle:

- Built after measured iterations and metric computation.

Thread safety:

- Immutable after construction.

Serialization:

- JSON serializable.

Validation:

- Metrics must include units and sources.

Error handling:

- Failed result includes classified error details.

### 3.3 `ExecutionContext`

Purpose: Runtime context for one benchmark lifecycle.

Attributes:

- `session_id`
- `configuration`
- `backend`
- `workload`
- `device`
- `profilers`
- `clock`
- `output_paths`

Methods:

- `open_scope(name)`
- `emit_progress(event)`
- `record_diagnostic(diagnostic)`

Relationships:

- Created by benchmark service.
- Passed through lifecycle components.

Lifecycle:

- Created after provider resolution.
- Destroyed after cleanup.

Thread safety:

- Not shared across concurrent sessions unless explicitly synchronized.

Serialization:

- Not persisted directly; selected fields are captured in session records.

Validation:

- Requires resolved providers and safe output paths.

Error handling:

- Records non-fatal diagnostics.

### 3.4 `BenchmarkBackend`

Purpose: Abstract contract for executing workloads.

Attributes:

- `name`
- `version`
- `capabilities`

Methods:

- `validate(workload, device, configuration)`
- `prepare(context)`
- `execute(context, iteration)`
- `cleanup(context)`

Relationships:

- Implemented by CPU, PyTorch, ONNX Runtime, TFLite, simulator, embedded, and plugin backends.

Lifecycle:

- Discovered by registry.
- Prepared before warmup.
- Executed during warmup and measurement.
- Cleaned up after execution.

Thread safety:

- Backend implementations declare whether instances are reusable or single-session.

Serialization:

- Backend metadata is serialized, backend object is not.

Validation:

- Capability validation occurs before execution.

Error handling:

- Raises backend-classified errors.

### 3.5 `Profiler`

Purpose: Capture measurements around execution scopes.

Attributes:

- `name`
- `version`
- `capabilities`
- `sampling_interval`

Methods:

- `start(scope)`
- `stop(scope)`
- `samples()`
- `summary()`

Relationships:

- Attached to benchmark lifecycle scopes.

Lifecycle:

- Initialized before measured execution.
- Started and stopped around configured scopes.
- Finalized before metric aggregation.

Thread safety:

- Profiler thread safety is provider-declared.

Serialization:

- Samples and summaries are persisted.

Validation:

- Profiler validates platform support and permissions.

Error handling:

- Recoverable failures become diagnostics where possible.

### 3.6 `Metric`

Purpose: Unit-bearing measurement or derived value.

Attributes:

- `name`
- `display_name`
- `value`
- `unit`
- `kind`
- `source`
- `assumptions`
- `higher_is_better`
- `tags`

Methods:

- `format()`
- `with_unit(unit)`
- `compare_to(other)`

Relationships:

- Produced by metric providers.
- Consumed by reports, visualizations, and comparisons.

Lifecycle:

- Created during metric computation.
- Immutable afterward.

Thread safety:

- Immutable.

Serialization:

- JSON and CSV safe.

Validation:

- Requires explicit unit and source.

Error handling:

- Invalid comparisons raise metric compatibility errors.

### 3.7 `MetricProvider`

Purpose: Compute one or more metrics.

Attributes:

- `name`
- `version`
- `required_inputs`
- `provided_metrics`

Methods:

- `can_compute(session)`
- `compute(session)`

Relationships:

- Registered by built-ins or plugins.

Lifecycle:

- Discovered at startup or provider resolution.
- Invoked after raw observations exist.

Thread safety:

- Providers should be stateless or declare state constraints.

Serialization:

- Provider metadata is persisted.

Validation:

- Required inputs are checked before compute.

Error handling:

- Missing inputs produce unavailable metric diagnostics.

### 3.8 `HardwareProfile`

Purpose: Capture host and target hardware context.

Attributes:

- `host`
- `cpu`
- `memory`
- `gpu`
- `accelerators`
- `embedded_target`
- `simulator`
- `drivers`
- `firmware`
- `power`
- `thermal`

Methods:

- `summary()`
- `capability(name)`
- `to_dict()`

Relationships:

- Produced by hardware inspectors.
- Stored in sessions.

Lifecycle:

- Captured before execution.
- Immutable inside finalized session.

Thread safety:

- Immutable after capture.

Serialization:

- JSON serializable with unavailable fields explicit.

Validation:

- Unknown vendor-specific fields are namespaced.

Error handling:

- Missing hardware details are warnings, not fabricated values.

### 3.9 `ModelMetadata`

Purpose: Describe benchmark workload identity and shape.

Attributes:

- `model_id`
- `name`
- `format`
- `source`
- `size_bytes`
- `input_shapes`
- `output_shapes`
- `precision`
- `parameters`
- `macs`
- `flops_estimate`
- `metadata`

Methods:

- `fingerprint()`
- `summary()`
- `to_dict()`

Relationships:

- Produced by model loaders or backends.
- Used by metrics and reports.

Lifecycle:

- Captured during preparation.
- Immutable in session.

Thread safety:

- Immutable.

Serialization:

- JSON serializable.

Validation:

- Estimates require assumptions.

Error handling:

- Unsupported metadata extraction is reported as diagnostic.

### 3.10 `PluginMetadata`

Purpose: Describe installed plugin compatibility and providers.

Attributes:

- `name`
- `version`
- `api_version`
- `package`
- `description`
- `providers`
- `dependencies`
- `capabilities`
- `status`
- `diagnostics`

Methods:

- `is_compatible(core_api_version)`
- `provider_names()`
- `to_diagnostic()`

Relationships:

- Produced by plugin manager.
- Stored in session metadata when plugin providers are used.

Lifecycle:

- Discovered during provider registry initialization.

Thread safety:

- Immutable after validation.

Serialization:

- JSON serializable.

Validation:

- Descriptor schema and API version are mandatory.

Error handling:

- Invalid plugins are isolated and diagnosed.

### 3.11 `Configuration`

Purpose: Represent resolved benchmark configuration.

Attributes:

- `schema_version`
- `sources`
- `profile`
- `workload`
- `backend`
- `device`
- `execution`
- `profiling`
- `metrics`
- `reports`
- `storage`
- `plugins`
- `tags`

Methods:

- `explain_sources()`
- `to_resolved_yaml()`
- `validate_for(command)`

Relationships:

- Created by configuration manager.
- Consumed by application services.

Lifecycle:

- Built before use-case execution.
- Persisted with sessions.

Thread safety:

- Immutable after resolution.

Serialization:

- YAML and JSON.

Validation:

- Schema validation and command-specific validation.

Error handling:

- Invalid configuration produces actionable configuration errors.

### 3.12 `ExportArtifact`

Purpose: Describe generated report or export files.

Attributes:

- `artifact_id`
- `kind`
- `format`
- `path`
- `sha256`
- `created_at`
- `source_session_ids`
- `metadata`

Methods:

- `verify_checksum()`
- `relative_path(root)`
- `to_manifest_entry()`

Relationships:

- Owned by session or comparison output.

Lifecycle:

- Created after successful report/export write.

Thread safety:

- Immutable.

Serialization:

- JSON serializable.

Validation:

- Path must be under allowed artifact root.

Error handling:

- Checksum mismatch produces artifact integrity error.

## 4. Interface Design

### 4.1 Python API

The Python API exposes typed services and models. It accepts structured command/configuration objects and returns typed result objects. It does not print to stdout.

Required surfaces:

- Benchmark execution.
- Profiling.
- Comparison.
- Reporting.
- Export.
- Configuration loading.
- Plugin diagnostics.
- Session loading.

### 4.2 CLI API

Required commands:

- `benchmark`
- `profile`
- `compare`
- `report`
- `dashboard`
- `export`
- `doctor`
- `version`

The CLI supports interactive Rich output, quiet output, verbose diagnostics, and JSON output for automation.

### 4.3 Plugin API

Plugins expose descriptors through Python entry points and register providers. Provider contracts are versioned. Plugin compatibility failures are diagnostics, not process-wide crashes unless strict mode is enabled.

### 4.4 Configuration API

The configuration API loads defaults, JSON, YAML, environment variables, and CLI overrides. It validates schemas, resolves profiles, explains sources, and emits a resolved configuration artifact.

### 4.5 Benchmark API

The benchmark API accepts workload, backend, device, execution, profiling, metrics, storage, and report settings. It returns a benchmark session or classified failure result.

### 4.6 Visualization API

The visualization API accepts metrics, observations, profiles, and comparison data and returns chart specifications or rendered artifacts.

### 4.7 Reporting API

The reporting API accepts session or comparison data and produces report artifacts with manifests and checksums.

### 4.8 Hardware API

The hardware API exposes discovery, selection, capability validation, metadata capture, and target diagnostics.

### 4.9 Model API

The model API exposes workload loading, metadata extraction, input specification, compatibility validation, and format-specific adapters.

### 4.10 Export API

The export API writes structured session or comparison data in JSON, CSV, Markdown, HTML, and future PDF formats while preserving provenance.

## 5. Plugin System

### 5.1 Design Goals

The plugin system follows the proven shape of pytest, mkdocs, and setuptools: entry-point discovery, descriptor validation, provider registration, and clear extension contracts.

### 5.2 Entry Point Group

Plugins are discovered under:

```text
aihw_bench.plugins
```

### 5.3 Plugin Descriptor

Required fields:

- `name`
- `version`
- `api_version`
- `description`
- `providers`
- `dependencies`
- `capabilities`

### 5.4 Provider Types

Supported provider families:

- Hardware inspectors.
- Benchmark backends.
- Model loaders.
- Metric providers.
- Reporters.
- Visualizers.
- Exporters.
- CLI commands.
- Third-party integrations.

### 5.5 Validation

The plugin manager validates descriptor schema, API version, duplicate names, provider contracts, dependency availability, and capability metadata.

### 5.6 Isolation

Initial plugins run in process and are trusted. Future plugin isolation may support subprocesses, remote providers, signed manifests, and trust policies.

### 5.7 Diagnostics

Plugin diagnostics include plugin name, package, provider, failure cause, impact, and suggested fix.

## 6. Data Model

Core persisted objects:

- `BenchmarkSession`: immutable top-level run record.
- `BenchmarkResult`: aggregate result for a workload/backend/device.
- `HardwareProfile`: host and target hardware metadata.
- `ExecutionContext`: non-persisted runtime execution context.
- `Metric`: unit-bearing measured or derived value.
- `ModelMetadata`: workload identity and model properties.
- `RunHistory`: historical comparison metadata.
- `PluginMetadata`: plugin descriptor and provider state.
- `Configuration`: resolved configuration.
- `ExportArtifact`: generated artifact metadata and checksum.

All persisted objects include schema version and must support future migration readers.

## 7. Workflows

### 7.1 Benchmark Workflow

1. Parse command or API request.
2. Resolve configuration.
3. Load plugin registry.
4. Resolve backend, model loader, hardware inspector, profilers, metrics, reporters, and exporters.
5. Create session.
6. Inspect hardware.
7. Load workload metadata.
8. Validate capability.
9. Prepare backend.
10. Run warmup.
11. Run measured iterations.
12. Stop profilers.
13. Compute metrics.
14. Persist session.
15. Generate configured artifacts.
16. Cleanup resources.
17. Return result and diagnostics.

### 7.2 Report Generation Workflow

1. Load session or comparison.
2. Build report view model.
3. Generate visualization specs.
4. Render requested formats.
5. Compute artifact checksums.
6. Update artifact manifest.

### 7.3 Plugin Loading Workflow

1. Scan entry points.
2. Load descriptors.
3. Validate metadata.
4. Register providers.
5. Record diagnostics.
6. Resolve providers by capability.

### 7.4 Visualization Workflow

1. Select chart family.
2. Validate required data.
3. Normalize units.
4. Downsample if needed.
5. Build chart specification.
6. Render or embed into report.

### 7.5 Export Workflow

1. Select session or comparison.
2. Select format.
3. Build export view model.
4. Write artifact under safe path.
5. Compute checksum.
6. Record manifest entry.

### 7.6 Release Workflow

1. Push semantic version tag.
2. Validate tag, package version, and changelog.
3. Run lint, formatting, type checks, tests, security scans, docs build, and package build.
4. Build wheel, source distribution, SBOM, checksums, and downstream metadata.
5. Verify installation on Windows, Linux, and macOS.
6. Publish GitHub Release, TestPyPI, PyPI, docs, and configured container images.

## 8. Configuration Design

### 8.1 Hierarchy

Precedence:

```text
CLI
Environment Variables
YAML
JSON
Defaults
```

If YAML and JSON files are both supplied, the explicitly selected file order is used within the configuration-file precedence layer. CLI and environment overrides still dominate file values.

### 8.2 Validation

Validation occurs before provider preparation. Errors include field path, rejected value, expected constraint, and suggested fix.

### 8.3 Profiles

Profiles support reusable benchmark configurations such as `quick`, `ci`, `accurate`, `embedded`, and `simulator`. Profile inheritance is acyclic.

### 8.4 Overrides

Overrides are typed and command-specific. Unknown keys are rejected in strict mode.

### 8.5 Persistence

The resolved configuration is persisted as a canonical session artifact.

## 9. Error Handling

### 9.1 Exceptions

Expected exception families:

- Configuration.
- Validation.
- Backend.
- Runtime.
- Profiler.
- Metric.
- Plugin.
- Storage.
- Report.
- Export.
- Security.
- Internal.

### 9.2 Logging

Logs are structured, redact secrets, and include correlation identifiers such as session ID, provider name, and phase.

### 9.3 Recovery

The engine preserves partial sessions when safe. Cleanup runs after recoverable failures. Report failures do not invalidate benchmark measurement.

### 9.4 Retries

Retries are configured per backend or execution plan. Retry metadata is stored with execution results.

### 9.5 Diagnostics

Diagnostics are user-facing records with cause, impact, suggested solution, and documentation reference.

### 9.6 CLI Errors

CLI errors are concise and actionable. Verbose mode reveals diagnostic details without exposing secrets.

## 10. Performance Design

### 10.1 Caching

Cache deterministic values only:

- Parsed configuration.
- Plugin descriptors.
- Backend capabilities.
- Model metadata fingerprints.
- Report templates.

### 10.2 Memory Management

Measured regions avoid report generation, unnecessary copies, and avoidable allocation. Large observations can be streamed in future storage backends.

### 10.3 Parallel Execution

Parallel execution is future scheduler-owned. It must isolate devices, profilers, output paths, seeds, and backend state.

### 10.4 Concurrency

Shared registries are immutable after initialization. Mutable execution state is session-local.

### 10.5 Lazy Loading

Optional heavy runtimes and vendor SDKs are imported only inside relevant adapters.

### 10.6 Streaming

Large benchmark campaigns should stream observations and write incremental artifacts without loading entire histories into memory.

### 10.7 Large Dataset Handling

Datasets and inputs are referenced through workload metadata and backend-specific loaders. The core package does not eagerly materialize large datasets.

## 11. Security Design

### 11.1 Dependency Verification

Release workflows include dependency auditing and SBOM generation.

### 11.2 Plugin Isolation

Initial plugin trust is explicit. Plugin descriptors are validated, plugin failures are isolated, and future subprocess isolation is reserved.

### 11.3 Input Validation

All external input is validated at CLI, API, configuration, plugin, model, session, and report boundaries.

### 11.4 Secure File Handling

Paths are resolved safely. Path traversal is rejected. Canonical session files are immutable after finalization.

### 11.5 Secure Configuration

Configuration is data only. It does not execute code. Secret values are not written to resolved configuration unless future secret-reference support explicitly marks them safe.

### 11.6 Supply Chain Security

Releases include checksums, SBOMs, trusted publishing where available, and future support for signatures and provenance.

## 12. Testability

### 12.1 Dependency Injection

Application services receive ports and clocks through constructors. This allows fake backends, stores, clocks, profilers, and reporters.

### 12.2 Mocking

Mocking is used at system boundaries. Domain logic should prefer real value objects and deterministic fixtures.

### 12.3 Fixtures

Fixtures include small models, fake sessions, malformed configs, plugin descriptors, sample reports, and corrupted session files.

### 12.4 Integration Testing

Integration tests cover configuration to session persistence, CLI to application service, report generation, plugin loading, and package install smoke checks.

### 12.5 Regression Testing

Regression tests preserve fixes for malformed files, missing dependencies, plugin failures, corrupted sessions, unsafe paths, and metric edge cases.

### 12.6 Performance Testing

Performance tests measure framework overhead, metric aggregation speed, report generation time, and large-session behavior.

## 13. Observability

### 13.1 Logging

Structured logs include session ID, phase, provider, backend, command, severity, and diagnostic code.

### 13.2 Tracing

Future tracing should expose benchmark lifecycle spans, backend preparation, measured execution, metric computation, report generation, and storage operations.

### 13.3 Metrics

Internal framework metrics include startup time, provider load time, benchmark overhead, report generation time, storage write time, and plugin diagnostics count.

### 13.4 Profiling

Framework self-profiling is separate from workload profiling and is used to maintain low overhead.

### 13.5 Debugging Support

Debug mode exposes resolved configuration, provider registry state, diagnostics, and safe environment metadata.

## 14. Release Engineering

### 14.1 GitHub Actions

Required workflows:

- CI quality gates.
- Documentation build and deploy.
- Package build.
- Tag-driven release.

### 14.2 GitHub Releases

Tag releases produce release notes, artifacts, checksums, SBOM, and generated downstream metadata.

### 14.3 PyPI and TestPyPI

Publishing uses trusted publishing. TestPyPI runs before PyPI when configured.

### 14.4 GitHub Pages

Documentation deploys automatically through GitHub Pages.

### 14.5 Container Images

Docker images are built and pushed when registry credentials are configured. Docker Hub and GHCR are supported release targets.

### 14.6 Downstream Package Managers

The design supports Conda-Forge, Homebrew, Winget, Chocolatey, Snapcraft, AUR, and Nix through generated metadata, documentation, and future automation.

### 14.7 Trusted Publishing

Registry publication should use identity-based trusted publishing rather than long-lived tokens where supported.

### 14.8 SBOM

Every release includes an SBOM artifact.

### 14.9 Signed Releases

The release design reserves support for signed artifacts and provenance attestations.

### 14.10 Semantic Versioning

Tags use `vMAJOR.MINOR.PATCH`. Package metadata uses `MAJOR.MINOR.PATCH`. The release pipeline fails if they do not match.

## 15. Documentation Design

### 15.1 Architecture Docs

Architecture docs describe layers, dependencies, subsystem boundaries, workflows, and extension contracts.

### 15.2 Developer Docs

Developer docs describe setup, quality gates, contribution standards, testing, architecture rules, and release workflows.

### 15.3 API Docs

API docs are generated from typed public interfaces and include examples, exceptions, versioning notes, and deprecation information.

### 15.4 CLI Docs

CLI docs include command descriptions, options, examples, output modes, exit codes, and troubleshooting.

### 15.5 Tutorials

Tutorials guide users from first benchmark through advanced comparison, plugin development, and report generation.

### 15.6 Examples

Examples include configurations, benchmark runs, report outputs, plugin skeletons, and CI snippets.

### 15.7 Plugin Guide

Plugin docs cover descriptor schema, provider contracts, version compatibility, diagnostics, packaging, and conformance tests.

### 15.8 Contributor Guide

Contributor docs explain architecture, branch workflow, issue triage, PR requirements, review standards, and release expectations.

## 16. Implementation Plan

### 16.1 Repository Foundation

Establish project metadata, governance, documentation, CI, release workflow, package layout, coding standards, and contribution standards.

### 16.2 Core Infrastructure

Implement domain models, ports, error hierarchy, utility helpers, configuration resolver, and session store foundation.

### 16.3 Benchmark Engine

Implement lifecycle state machine, fake/reference backend, warmup, measured execution, failure classification, progress events, and persistence.

### 16.4 Hardware Layer

Implement host hardware inspector, device selector, capability model, and backend capability validation.

### 16.5 Model Layer

Implement workload model, metadata extraction contracts, input specification, and initial model loaders.

### 16.6 Metrics Engine

Implement primary latency, throughput, FPS, memory, utilization, model size, MAC, FLOPS estimate, arithmetic intensity, and comparison metrics.

### 16.7 Visualization

Implement chart specification models and initial timeline, latency, memory, scaling, comparison, and utilization chart providers.

### 16.8 Reporting

Implement JSON, CSV, Markdown, HTML, and later PDF reports with report view models and artifact manifests.

### 16.9 Plugin System

Implement entry-point discovery, descriptor validation, provider registry, diagnostics, conformance tests, and example plugins.

### 16.10 Testing

Implement unit, integration, CLI, regression, optional backend, performance, compatibility, and release validation tests.

### 16.11 Packaging

Implement package extras, build validation, install verification, Docker image, Conda metadata, Homebrew formula generation, and downstream packaging docs.

### 16.12 Documentation

Build user guide, developer guide, API reference, CLI reference, tutorials, examples, plugin guide, troubleshooting, and architecture docs.

### 16.13 Release

Finalize semantic versioning, changelog process, GitHub Releases, PyPI/TestPyPI trusted publishing, GitHub Pages, SBOMs, checksums, install verification, and future signed provenance.
