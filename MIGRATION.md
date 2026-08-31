# Migration Guide

## Migrating From Pre-1.0 Snapshots To v1.0.0

AIHW-Bench v1.0.0 is the first stable release. Earlier repository snapshots were milestone-oriented and may have described planned APIs before implementation.

## Package Installation

Use the stable package name:

```bash
pip install aihw-bench
```

For local development:

```bash
python -m pip install -e .
```

## Python API

Prefer imports from the public package where possible:

```python
from aihw_bench import BenchmarkRequest, BenchmarkService, Configuration
```

Application, domain, and infrastructure modules remain documented for advanced users, but the public package exports are the stable first choice for common integration.

## CLI

Use the implemented command set:

```bash
aihw-bench benchmark
aihw-bench profile
aihw-bench compare
aihw-bench report
aihw-bench export
aihw-bench config
aihw-bench doctor
aihw-bench version
```

The previously planned `dashboard` command is not part of v1.0.0. Dashboard-ready visualization components are available through the visualization and reporting APIs.

## Configuration

Configuration resolution is stable in this precedence order:

1. Built-in defaults.
2. YAML or JSON file.
3. `AIHW_BENCH_` environment variables.
4. CLI overrides.

Use `aihw-bench config --output yaml` to inspect resolved values.

## Plugins

Plugins must expose the `aihw_bench.plugins` entry point and return `PluginRegistration` or `PluginManifest`. The v1.0 plugin API version is `1.0`; incompatible plugin API versions are rejected.

## Reports

Reports are generated from finalized sessions. Supported formats are `json`, `csv`, `markdown`, and `html`.
