# Examples

Use `examples/configs/reference-benchmark.yaml` for a deterministic smoke benchmark:

```bash
aihw-bench benchmark --config examples/configs/reference-benchmark.yaml
```

This directory contains release-quality examples for AIHW-Bench users and plugin authors.

Examples are organized by purpose:

- `configs`: benchmark configuration files.
- `plugins`: plugin package examples.
- `reports`: representative report outputs and report fixtures.

Every example added here must match implemented behavior, be documented, and be validated by the test or documentation workflow once its target subsystem exists.
