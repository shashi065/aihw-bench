# Benchmark Engine Design

## Purpose

The benchmark engine coordinates workload execution while minimizing overhead in measured regions and preserving enough metadata for reproducibility.

## Implementation Status

Milestone 2 implements the benchmark engine as an application service with a deterministic execution scheduler, high-resolution timing helpers, summary statistics, and a built-in reference backend for smoke validation.

Public entry points are exposed from `aihw_bench.application`.

```python
from aihw_bench.application import BenchmarkRequest, BenchmarkService, ScriptedTimingEngine
from aihw_bench.domain.models import Configuration, ExecutionConfig
from aihw_bench.infrastructure.backends import ReferenceBenchmarkBackend

service = BenchmarkService(
  ReferenceBenchmarkBackend(),
  timing_engine=ScriptedTimingEngine([0.02, 0.03, 0.04]),
)

outcome = service.run(
  BenchmarkRequest(
    session_id="benchmark-demo",
    configuration=Configuration(execution=ExecutionConfig(warmup_iterations=1, iterations=2)),
  )
)
```

## Lifecycle

### Initialization

- Resolve configuration.
- Load plugin providers.
- Select backend, device, workload, profilers, metrics, and reporters.
- Inspect host and target hardware.
- Validate backend capability.
- Create pending session record.

### Preparation

- Load model or workload representation.
- Prepare backend runtime resources.
- Allocate or generate input data.
- Calibrate optional profilers.
- Record preparation diagnostics.

### Warmup

- Execute configured warmup iterations.
- Exclude warmup from primary metrics.
- Store warmup timing separately.
- Detect early runtime failures.

### Execution

- Execute measured iterations.
- Use monotonic high-resolution timing.
- Keep measured regions small.
- Capture backend observations and profiler samples.
- Apply timeout and retry policy.

### Measurement

- Record raw observations before aggregation.
- Preserve per-iteration latency.
- Capture status for every iteration.
- Associate profiler samples with execution scopes.

### Statistics

- Compute min, max, mean, median, standard deviation, percentiles, throughput, FPS, memory summaries, utilization summaries, and derived estimates.
- Record assumptions for estimated metrics.
- Mark unavailable metrics explicitly.

### Aggregation

- Aggregate by workload, backend, device, precision, batch size, and tags.
- Keep raw observations immutable.
- Compute comparison-ready summary records.

### Export

- Persist canonical session data.
- Generate requested report and export artifacts.
- Write checksums for artifacts when release-grade reproducibility is requested.

### Cleanup

- Release backend resources.
- Stop profilers.
- Flush artifacts.
- Finalize session status.

### Recovery

- Failed runs are stored with error metadata.
- Partial sessions remain inspectable.
- Cleanup failures are recorded as diagnostics.
- The engine avoids corrupting finalized sessions.

## State Machine

```text
created -> configured -> prepared -> warming -> measuring -> aggregating -> reporting -> finalized
                               |             |             |             |
                               v             v             v             v
                             failed        failed        failed        partial
```

## Error Policy

Expected failures are classified as configuration, validation, backend, runtime, timeout, profiler, storage, or report errors. Fatal failures stop the session. Recoverable failures produce diagnostics and degraded results.

## Concurrency

The initial engine runs one benchmark plan at a time. The architecture reserves a scheduler boundary for future parallel and distributed execution. Parallel execution must isolate devices, output paths, random seeds, profiler state, and backend resources.

## Determinism

Benchmark sessions record configuration, hardware metadata, software versions, backend versions, seed policy, input metadata, model metadata, and plugin metadata.
