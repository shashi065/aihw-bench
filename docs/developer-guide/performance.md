# Performance Guide

Benchmark code must protect measured regions from avoidable overhead.

Core practices:

- Prepare models, inputs, and backend state outside measured loops.
- Use monotonic high-resolution clocks.
- Separate warmup runs from measured runs.
- Collect heavy profiler data only when requested.
- Generate reports after measurement completes.
- Preserve raw observations so metric algorithms can evolve without rerunning workloads.
