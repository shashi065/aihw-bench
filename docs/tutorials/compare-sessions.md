# Tutorial: Compare Sessions

The compare command reads two stored sessions and compares a named numeric metric.

## Generate Two Sessions

Run the benchmark twice with different configuration files, environment variables, or backend settings.

```bash
aihw-bench benchmark --config examples/configs/reference-benchmark.yaml
aihw-bench benchmark --config examples/configs/reference-benchmark.yaml
```

Record the two session IDs printed by the CLI.

## Compare Latency

```bash
aihw-bench compare BASELINE_SESSION CANDIDATE_SESSION --metric latency_mean_seconds
```

For automation, use JSON output:

```bash
aihw-bench compare BASELINE_SESSION CANDIDATE_SESSION \
  --metric latency_mean_seconds \
  --output json
```

## Interpret The Result

The comparison reports the baseline value, candidate value, and delta. Lower latency is better for latency metrics; higher throughput is better for throughput metrics.
