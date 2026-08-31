# Data Model

AIHW-Bench data models preserve reproducibility. Every persisted object records schema version, units, timestamps where relevant, and provenance.

## Common Model Rules

- Identifiers are stable strings.
- Timestamps use UTC with explicit timezone.
- Durations use seconds unless a model explicitly states another unit.
- Numeric metrics store value and unit separately.
- Backend-specific metadata is namespaced.
- Persisted models include a schema version.

## `BenchmarkSession`

Purpose: Top-level immutable record for one benchmark invocation.

Fields:

- `session_id`: unique identifier.
- `schema_version`: persisted schema version.
- `created_at`: UTC timestamp.
- `completed_at`: UTC timestamp when finalized.
- `status`: completed, failed, cancelled, or partial.
- `configuration`: resolved configuration snapshot.
- `hardware`: hardware information snapshot.
- `system`: OS, Python, package, environment, and dependency metadata.
- `workload`: model and input metadata.
- `backend`: selected backend and capability metadata.
- `runs`: measured and warmup run records.
- `metrics`: computed metric records.
- `profiles`: profiler output summaries.
- `artifacts`: generated reports and exports.
- `diagnostics`: warnings and recoverable errors.

## `BenchmarkResult`

Purpose: Aggregate result for a workload/backend/device combination.

Fields:

- `result_id`
- `session_id`
- `status`
- `primary_metrics`
- `secondary_metrics`
- `statistics`
- `summary`
- `comparison_keys`
- `error`

## `Metric`

Purpose: Store a measured or derived quantity.

Fields:

- `name`
- `display_name`
- `value`
- `unit`
- `kind`: measured, derived, estimated, metadata.
- `source`: backend, profiler, metric provider, user metadata.
- `higher_is_better`
- `assumptions`
- `precision`
- `tags`

## `HardwareInfo`

Purpose: Capture target and host hardware metadata.

Fields:

- `host_name`
- `cpu`
- `memory`
- `gpu`
- `accelerators`
- `embedded_target`
- `simulator`
- `driver_versions`
- `firmware_versions`
- `thermal_policy`
- `power_policy`

## `ModelInfo`

Purpose: Describe the benchmarked workload.

Fields:

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

## `ExecutionResult`

Purpose: Store one backend execution event.

Fields:

- `execution_id`
- `phase`: warmup, measurement, calibration, cleanup.
- `iteration`
- `started_at`
- `ended_at`
- `duration_seconds`
- `status`
- `observations`
- `backend_metadata`
- `error`

## `Profile`

Purpose: Store profiler samples and summaries.

Fields:

- `profile_id`
- `profiler_name`
- `scope`
- `sampling_interval_seconds`
- `samples`
- `summary`
- `diagnostics`

## `RunHistory`

Purpose: Support historical comparison and regression analysis.

Fields:

- `history_id`
- `session_ids`
- `comparison_keys`
- `baseline_session_id`
- `candidate_session_id`
- `deltas`
- `thresholds`
- `outcomes`

## `Configuration`

Purpose: Store resolved benchmark configuration.

Fields:

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

## `PluginMetadata`

Purpose: Describe a discovered plugin and its providers.

Fields:

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

## Schema Evolution

Persisted data models evolve through schema versions. Readers should support migration from supported older schemas. Writers emit only the current schema. Breaking schema changes require release notes and migration documentation.
