# Official Benchmark Fixtures

This directory contains the deterministic, synthetic input manifests and reference-backend baseline fixture for the AIHW-Bench v1.3 official suite. Regenerate them with:

```bash
aihw-bench suite materialize --output-dir examples/benchmarks/datasets
aihw-bench suite baselines --output-dir examples/benchmarks
```

The manifests contain per-sample seeds and SHA-256 checksums; they do not include third-party datasets or model weights. See `docs/benchmarks/official-suite.md` for each benchmark contract.
