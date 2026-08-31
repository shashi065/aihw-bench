# Migration Guide

AIHW-Bench v1.0.0 is the first stable release. Earlier pre-1.0 snapshots were milestone-oriented and may have included planned APIs or documentation ahead of implementation.

## Install The Stable Package

```bash
pip install aihw-bench
```

For local source development:

```bash
python -m pip install -e .
```

## Update Python Imports

Prefer stable public package imports:

```python
from aihw_bench import BenchmarkRequest, BenchmarkService, Configuration
```

Advanced integrations can continue to import documented application, domain, and infrastructure modules.

## Update CLI Usage

The stable command set is:

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

The planned `dashboard` command is not included in v1.0.0. Use report and visualization APIs for dashboard-ready chart components.

## Update Configuration Workflows

Configuration precedence is:

1. Built-in defaults.
2. YAML or JSON file.
3. `AIHW_BENCH_` environment variables.
4. CLI overrides.

Run this before automation changes:

```bash
aihw-bench config --config path/to/config.yaml --output yaml
```

## Update Plugins

Plugins must use plugin API version `1.0` and expose an `aihw_bench.plugins` entry point returning `PluginRegistration` or `PluginManifest`.

## Update Reports

Reports are generated from finalized sessions. Supported formats are `json`, `csv`, `markdown`, and `html`.
