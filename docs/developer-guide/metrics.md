# Metrics

Milestone 5 introduces the core metrics engine used by benchmark results and downstream reports.

## Scope

The built-in `CoreMetricsEngine` computes metrics from successful measured iterations only. Warmup runs remain in the session record but are excluded from primary latency, throughput, resource, utilization, and FLOPS calculations.

## Core Metrics

| Metric | Unit | Kind | Source |
| --- | --- | --- | --- |
| `latency_mean_seconds` | seconds | derived | measured iteration duration |
| `latency_min_seconds` | seconds | derived | measured iteration duration |
| `latency_max_seconds` | seconds | derived | measured iteration duration |
| `latency_median_seconds` | seconds | derived | measured iteration duration |
| `latency_p95_seconds` | seconds | derived | measured iteration duration |
| `latency_p99_seconds` | seconds | derived | measured iteration duration |
| `latency_stdev_seconds` | seconds | derived | measured iteration duration |
| `benchmark_duration_total_seconds` | seconds | derived | measured iteration duration |
| `throughput_iterations_per_second` | iterations/s | derived | measured count divided by measured duration |
| `throughput_samples_per_second` | samples/s | derived | iteration throughput multiplied by batch size |
| `memory_mean_bytes` | bytes | measured or unavailable | backend observations |
| `memory_max_bytes` | bytes | measured or unavailable | backend observations |
| `cpu_utilization_mean_percent` | percent | measured or unavailable | backend observations |
| `cpu_utilization_max_percent` | percent | measured or unavailable | backend observations |
| `gpu_utilization_mean_percent` | percent | measured or unavailable | backend observations |
| `gpu_utilization_max_percent` | percent | measured or unavailable | backend observations |
| `estimated_flops_per_second` | FLOP/s | estimated or unavailable | workload metadata or backend observations |

## Observation Keys

Backends can provide optional measured resource values in each execution observation. The core engine recognizes these aliases:

- Memory: `memory_peak_bytes`, `peak_memory_bytes`, `memory_usage_bytes`, `memory_bytes`, `process_memory_bytes`, `rss_bytes`.
- CPU utilization: `cpu_utilization_percent`, `cpu_percent`, `process_cpu_percent`.
- GPU utilization: `gpu_utilization_percent`, `gpu_percent`.
- Operation count: `flop_count`, `flops_estimate`, `flops`, `operation_count`, `macs`.

If a metric cannot be computed, AIHW-Bench emits an explicit `unavailable` metric with the expected unit and an assumption explaining the missing observation.

## FLOPS Estimation

FLOPS is estimated only when supported input data exists. The metrics engine uses the first available source in this order:

1. `ModelMetadata.flops_estimate`.
2. `ModelMetadata.macs * 2`.
3. Backend-reported operation count observation.

The selected operation count is multiplied by measured iteration throughput. FLOPS values are marked as `estimated` because static workload metadata and backend counters may not represent exact executed operations for every runtime.

## Reporting Integration

`BenchmarkResult.summary` contains a compact report-ready payload with session ID, backend, device, precision, batch size, measurement count, hardware summary, workload summary, primary metrics, resource metrics, and metric assumptions.

Report generators should use the structured `Metric` records for tables and the summary payload for headings, cards, and compact machine-readable exports.
