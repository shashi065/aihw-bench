# Example: Configuration Files

The reference configuration demonstrates the core settings needed for a benchmark session.

```yaml
profile: reference
backend:
  name: reference
  device: cpu
execution:
  warmup_iterations: 1
  iterations: 5
  timeout_seconds: 60
  batch_size: 1
  precision: fp32
reports:
  formats:
    - json
    - markdown
  output_dir: reports
```

Run it with:

```bash
aihw-bench benchmark --config examples/configs/reference-benchmark.yaml
```

Use `aihw-bench config --output yaml` to confirm the final resolved values.
