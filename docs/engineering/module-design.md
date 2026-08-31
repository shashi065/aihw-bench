# Module Design

This document defines the intended module responsibilities before implementation. Module names describe ownership boundaries, not final file counts.

## `aihw_bench.domain`

### Purpose

Own the business model for benchmarks, metrics, hardware, workloads, sessions, reports, plugins, and comparison rules.

### Responsibilities

- Define immutable entities and value objects.
- Define domain ports for backends, profilers, metrics, reports, visualizations, storage, and hardware inspection.
- Define policies for validation, regression classification, unit normalization, and result aggregation.

### Dependencies

Allowed dependencies are Python standard library, Pydantic for boundary models, and domain-local modules.

### Public APIs

- Benchmark session model.
- Benchmark result model.
- Metric model.
- Hardware and model information models.
- Domain port protocols.
- Domain exception hierarchy.

### Private Components

- Internal validators.
- Unit conversion helpers.
- Policy composition helpers.

### Configuration

Domain objects accept resolved configuration values only. The domain layer does not read files, environment variables, or CLI flags.

### Error Handling

Domain errors describe violated invariants and invalid state transitions. They do not contain terminal formatting.

### Testing Strategy

Unit tests validate constructors, invariants, equality semantics, serialization, aggregation policies, and error messages.

### Future Extensions

- Statistical confidence policies.
- Benchmark certification metadata.
- Distributed run topology models.

## `aihw_bench.application`

### Purpose

Coordinate use cases using domain ports and resolved configuration.

### Responsibilities

- Benchmark, profile, compare, report, export, doctor, and session orchestration.
- Dependency injection boundaries.
- Progress event emission.
- Transaction-style execution around session creation and finalization.

### Dependencies

May depend on `domain` and dependency-neutral utilities. Must not import CLI frameworks or concrete vendor runtimes.

### Public APIs

- Command objects such as benchmark, profile, compare, report, export, and doctor commands.
- Service classes for each use case.
- Result objects for application consumers.

### Private Components

- Use case execution planners.
- Provider resolution helpers.
- Progress event factories.

### Configuration

Receives resolved settings from the configuration subsystem. Does not know where values came from.

### Error Handling

Application errors classify configuration, capability, execution, persistence, and report failures. They wrap lower-level causes without erasing them.

### Testing Strategy

Use fake backends, fake stores, fake clocks, fake profilers, and in-memory reporters to test orchestration deterministically.

### Future Extensions

- Distributed execution scheduler.
- Remote lab controller.
- Long-running job persistence.

## `aihw_bench.infrastructure.backends`

### Purpose

Implement workload execution for concrete runtimes and hardware targets.

### Responsibilities

- CPU reference backend.
- PyTorch adapter.
- ONNX Runtime adapter.
- TensorFlow Lite adapter.
- Simulator and embedded adapter contracts.
- Backend capability detection.

### Dependencies

May depend on optional runtime packages only inside adapter modules. Core backend contracts remain dependency-light.

### Public APIs

Infrastructure providers are exposed through plugin registration or composition roots, not through direct user imports.

### Private Components

- Runtime-specific loaders.
- Device selectors.
- Precision mappers.
- Input generators.
- Adapter-specific error translators.

### Configuration

Each backend receives only its own typed backend configuration.

### Error Handling

Backend errors include missing dependency, unsupported capability, invalid model, runtime failure, timeout, and device unavailable classifications.

### Testing Strategy

Core tests use fake backends. Optional runtime tests run only when dependencies are installed. Backend conformance tests validate every adapter against the same contract.

### Future Extensions

- Vendor accelerator SDKs.
- Simulator transport protocols.
- Remote embedded execution.
- Compiler graph lowering integrations.

## `aihw_bench.infrastructure.hardware`

### Purpose

Collect host hardware and accelerator metadata needed for backend validation and session reproducibility.

### Responsibilities

- Host hardware inspection.
- GPU capability hints.
- Hardware profile normalization.

### Dependencies

May depend on standard library platform probes and optional runtime libraries only when present.

### Public APIs

- Hardware inspector.

### Private Components

- Memory snapshot helpers.
- Accelerator hint collectors.

### Configuration

Receives environment hints and optional inspector configuration.

### Error Handling

Hardware inspection failures fall back to explicit unavailable fields rather than fabricated values.

### Testing Strategy

Unit tests validate normalized snapshots and optional GPU hint handling.

### Future Extensions

- Remote hardware inventory.
- Power and thermal telemetry collectors.

## `aihw_bench.infrastructure.models`

### Purpose

Implement runtime-specific model loaders and a registry that resolves supported formats without coupling the domain layer to optional heavy dependencies.

### Responsibilities

- PyTorch and TorchScript loading.
- ONNX Runtime loading and graph validation.
- TensorFlow Lite loading and interpreter validation.
- Model metadata extraction.
- Optional dependency handling.

### Dependencies

May depend on optional runtime packages only inside adapter modules. Core model contracts remain dependency-light.

### Public APIs

- Model loader registry.
- Format-specific loader adapters.

### Private Components

- Import guards.
- Metadata extractors.
- Tensor information normalizers.

### Configuration

Receives workload source paths, desired framework hints, and model metadata overrides from resolved configuration.

### Error Handling

Model loading failures distinguish missing dependencies, unsupported formats, corrupted files, and incompatible runtime objects.

### Testing Strategy

Unit tests use fake runtime modules and temporary files. Integration tests validate benchmark-service resolution from configuration.

### Future Extensions

- Additional runtime formats.
- Identifier-based model registries.
- Remote model artifact fetchers.

## `aihw_bench.infrastructure.profiling`

### Purpose

Collect measurements around benchmark execution without owning benchmark lifecycle policy.

### Responsibilities

- CPU utilization sampling.
- Memory usage sampling.
- Optional GPU or accelerator sampling.
- Profiler scope management.

### Dependencies

May depend on platform libraries, optional vendor tools, and domain profiler ports.

### Public APIs

Profiler providers are registered through plugin descriptors or composition roots.

### Private Components

- Sampling loops.
- Platform-specific collectors.
- Unit normalization.

### Configuration

Receives sampling interval, profiler list, device selector, and collection scope.

### Error Handling

Profiling failures are recorded as degraded measurement diagnostics when benchmark execution can continue safely.

### Testing Strategy

Unit tests cover sample normalization. Integration tests validate profiler lifecycle with fake clocks.

### Future Extensions

- Trace import.
- Hardware counter support.
- Power and thermal telemetry.

## `aihw_bench.infrastructure.metrics`

### Purpose

Compute primary and derived metrics from raw observations and profiler samples.

### Responsibilities

- Latency statistics.
- Throughput and FPS.
- Memory statistics.
- Utilization summaries.
- Model complexity estimates.
- Arithmetic intensity and FLOPS estimates.

### Dependencies

May use NumPy and Pandas for deterministic aggregation where appropriate.

### Public APIs

Metric providers implement the domain metric provider port.

### Private Components

- Aggregation kernels.
- Unit conversion tables.
- Statistical helpers.

### Configuration

Receives enabled metrics, percentile settings, regression thresholds, and model metadata.

### Error Handling

Missing observations produce explicit unavailable metrics with causes rather than fabricated values.

### Testing Strategy

Golden-data tests validate metric stability. Property-style tests validate monotonic and unit invariants.

### Future Extensions

- Confidence intervals.
- Bootstrapped statistics.
- Energy efficiency metrics.

## `aihw_bench.infrastructure.storage`

### Purpose

Persist benchmark sessions, observations, metrics, reports, and metadata.

### Responsibilities

- Filesystem session store.
- Immutable session layout.
- Artifact write policy.
- Session listing and filtering.

### Dependencies

May depend on standard filesystem libraries and serialization utilities.

### Public APIs

Concrete storage implementations satisfy the `SessionStore` port.

### Private Components

- Safe path resolver.
- Atomic write helpers.
- Manifest builder.

### Configuration

Receives root output directory, retention policy, and write mode.

### Error Handling

Storage errors distinguish permission failure, path traversal attempt, corrupted session data, missing artifact, and incompatible schema version.

### Testing Strategy

Integration tests use temporary directories and verify immutability, atomic writes, and corrupted data handling.

### Future Extensions

- SQLite local store.
- PostgreSQL hosted store.
- Object storage backend.

## `aihw_bench.infrastructure.reporting`

### Purpose

Render benchmark and comparison data into durable report artifacts.

### Responsibilities

- HTML reports.
- Markdown reports.
- JSON reports.
- CSV exports.
- Future PDF reports.
- Recommendation text derived from metrics and policies.

### Dependencies

May use Jinja2, Pandas, Plotly, and serialization utilities.

### Public APIs

Reporter providers implement the report port.

### Private Components

- Templates.
- View models.
- Table builders.
- Artifact naming policy.

### Configuration

Receives report format, output path, theme, included sections, and visualization options.

### Error Handling

Report errors preserve template, serialization, and file output causes.

### Testing Strategy

Snapshot tests verify stable output structure. Integration tests validate generated artifacts from sample sessions.

### Future Extensions

- PDF renderer.
- Static dashboard bundle.
- Hosted report publishing.

## `aihw_bench.infrastructure.visualization`

### Purpose

Prepare chart specifications and interactive data models without executing benchmarks.

### Responsibilities

- Timeline charts.
- Roofline charts.
- Latency distribution charts.
- Memory charts.
- Scaling graphs.
- Comparison graphs.
- Hardware utilization charts.

### Dependencies

May use Plotly for chart generation and typed view models for report integration.

### Public APIs

Visualization providers implement the visualizer port.

### Private Components

- Chart data normalizers.
- Axis and unit policies.
- Theme adapters.

### Configuration

Receives chart type, theme, output mode, and downsampling settings.

### Error Handling

Visualization errors report missing data, incompatible units, or renderer failures.

### Testing Strategy

Unit tests validate chart data. Snapshot tests validate serialized chart specifications.

### Future Extensions

- Web dashboard components.
- Real-time run visualization.
- Large-session downsampling.

## `aihw_bench.infrastructure.plugins`

### Purpose

Discover, validate, and register third-party extensions.

### Responsibilities

- Entry point discovery.
- Descriptor validation.
- Provider registration.
- Compatibility checks.
- Plugin diagnostics.

### Dependencies

May use Python packaging metadata APIs and domain plugin models.

### Public APIs

Plugin authors interact with the plugin descriptor schema and provider interfaces.

### Private Components

- Entry point scanner.
- Compatibility resolver.
- Provider registry.

### Configuration

Receives enabled plugins, disabled plugins, strict mode, and plugin search policy.

### Error Handling

Plugin errors are isolated, classified, and exposed through diagnostics.

### Testing Strategy

Tests cover malformed descriptors, duplicate providers, incompatible versions, disabled plugins, and partial load failures.

### Future Extensions

- Out-of-process plugin execution.
- Signed plugin manifests.
- Plugin capability marketplace metadata.

## `aihw_bench.infrastructure.configuration`

### Purpose

Resolve configuration from defaults, files, environment variables, and CLI overrides.

### Responsibilities

- YAML and JSON loading.
- Environment variable parsing.
- Precedence merging.
- Profile inheritance.
- Schema validation.

### Dependencies

May use Pydantic settings, PyYAML, JSON, and path utilities.

### Public APIs

Configuration loader and resolved configuration models.

### Private Components

- Merge strategy.
- Environment key mapper.
- File format readers.

### Configuration

Self-configuration is limited to file locations and environment prefix.

### Error Handling

Errors distinguish malformed file, unsupported format, unknown key, invalid value, and unsafe path.

### Testing Strategy

Tests cover precedence, inheritance, validation, environment parsing, and malformed input.

### Future Extensions

- Remote configuration sources.
- Organization-level profiles.
- Encrypted secret references.

## `aihw_bench.presentation.cli`

### Purpose

Expose application use cases through a polished terminal interface.

### Responsibilities

- Command parsing.
- Rich human-readable output.
- Machine-readable output modes.
- Exit code mapping.
- User-friendly diagnostics.

### Dependencies

May depend on Typer, Rich, application services, and infrastructure composition roots.

### Public APIs

CLI commands are public user-facing APIs and follow semantic versioning once stable.

### Private Components

- Output renderers.
- Exit code mapper.
- CLI configuration override builder.

### Configuration

Reads CLI flags and converts them into override objects.

### Error Handling

Expected errors become concise messages with suggested fixes. Unexpected errors include debug guidance without exposing secrets.

### Testing Strategy

CLI tests validate exit codes, output modes, help text, and error behavior.

### Future Extensions

- Plugin-provided commands.
- Shell completion.
- Interactive local dashboard launcher.

## `aihw_bench.utils`

### Purpose

Provide dependency-neutral technical helpers used across layers.

### Responsibilities

- Unit formatting.
- Time abstractions.
- Path safety helpers.
- Hashing.
- Serialization helpers.
- Logging setup.

### Dependencies

Utilities should prefer the standard library and avoid importing application or infrastructure code.

### Public APIs

Utilities are internal unless explicitly promoted to the public API.

### Private Components

Small helper functions and constants.

### Configuration

Utilities do not read global configuration.

### Error Handling

Utility errors should be narrow and composable.

### Testing Strategy

Unit tests cover edge cases and platform-specific behavior.

### Future Extensions

- More unit systems.
- Stable schema hashing.
- Structured logging adapters.
