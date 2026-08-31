# Visualization System

## Purpose

The visualization system converts benchmark and profile data into charts and dashboard-ready specifications.

## Chart Families

### Timeline Charts

Show benchmark phases, iteration durations, profiler scopes, and failures over time.

### Roofline Charts

Compare arithmetic intensity and estimated FLOPS against theoretical hardware limits. Inputs must record assumptions for peak compute and memory bandwidth.

### Latency Distribution

Show per-iteration latency using histograms, box plots, percentile markers, and outlier indicators.

### Memory Charts

Show peak memory, average memory, allocation trends, and profiler-derived memory samples.

### Scaling Graphs

Show behavior across batch size, precision, backend, device, model, or concurrency level.

### Comparison Graphs

Show deltas between baseline and candidate sessions with threshold bands.

### Hardware Utilization

Show CPU, GPU, accelerator, simulator, memory, and future power or thermal utilization.

### Interactive Dashboard

Future dashboard visualizations consume the same chart specification models as static reports.

## Design Rules

- Visualization never executes benchmarks.
- Visualization never reads global state.
- Chart data uses explicit units.
- Downsampling must preserve extrema.
- Missing data is displayed explicitly.
- Chart generation should be deterministic for identical inputs.

## Future Extensions

- Live run progress charts.
- Multi-session exploration.
- Hosted dashboard backend.
- Power and energy charts.
