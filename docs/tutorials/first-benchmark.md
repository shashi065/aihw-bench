# Tutorial: First Benchmark

This tutorial runs the built-in reference benchmark and generates session artifacts.

## 1. Check The Environment

```bash
aihw-bench doctor
```

The command validates Python, core CLI dependencies, the plugin API, and plugin diagnostics.

## 2. Inspect The Configuration

```bash
aihw-bench config --config examples/configs/reference-benchmark.yaml --output yaml
```

The output shows the final configuration after defaults and file values are merged.

## 3. Run The Benchmark

```bash
aihw-bench benchmark \
  --config examples/configs/reference-benchmark.yaml \
  --storage-root .aihw-bench/sessions \
  --output-dir reports \
  --report json \
  --report markdown
```

The CLI displays progress while the benchmark service prepares the backend, executes warmup and measured iterations, computes metrics, stores the session, and renders reports.

## 4. Review Outputs

Session records are stored under `.aihw-bench/sessions`. Reports are written to the configured report directory.

Use the session ID from the benchmark output with:

```bash
aihw-bench report SESSION_ID --format html --output-dir reports
```

## 5. Automate The Workflow

For CI smoke tests, keep the reference backend and deterministic workload settings. For host-specific benchmarks, increase measured iterations and store the resulting session JSON with the environment metadata.
