# Plugin Development

Plugins are Python packages that expose an `aihw_bench.plugins` entry point returning a `PluginRegistration` or `PluginManifest`.
The plugin framework discovers those entry points, validates compatibility, registers providers, and isolates plugin failures as diagnostics unless strict mode is enabled.

## Entry Point

Declare an entry point in the plugin package:

```toml
[project.entry-points."aihw_bench.plugins"]
example = "aihw_bench_example_plugin:register_plugin"
```

The function must return a registration:

```python
from aihw_bench.application import PluginManifest, PluginProviderKind, PluginRegistration


def register_plugin() -> PluginRegistration:
    manifest = PluginManifest(
        name="example",
        version="0.1.0",
        api_version="1.0",
        package="aihw-bench-example-plugin",
        description="Example AIHW-Bench extension.",
        providers=(PluginProviderKind.METRICS,),
    )
    return PluginRegistration.from_manifest(
        manifest,
        providers={"metrics": {"example_metric": ExampleMetricProvider()}},
    )
```

## Supported Providers

Milestone 9 supports these provider categories:

- `hardware`: hardware inspectors, backend factories, or accelerator capability providers.
- `models`: model loaders or model metadata providers.
- `reports`: report renderers.
- `visualizations`: chart builders and dashboard components.
- `metrics`: metric providers.
- `cli_commands`: command factories for the Typer CLI composition root.
- `exporters`: artifact exporters.

Provider objects must satisfy the corresponding domain protocol where one exists, such as `BenchmarkBackend`, `MetricProvider`, `Reporter`, or `Visualizer`.

## Compatibility

The current plugin API version is `1.0`.
Plugins with a different `api_version` are rejected with a diagnostic.
Plugin dependencies are declared by plugin name and must be registered before dependent plugins activate.

```python
PluginManifest(
    name="vendor-reports",
    version="0.2.0",
    api_version="1.0",
    package="vendor-aihw-reports",
    description="Vendor report templates.",
    providers=(PluginProviderKind.REPORTS,),
    dependencies=("vendor-hardware",),
)
```

## Configuration

Plugin loading is controlled by the resolved configuration:

```yaml
plugins:
  enabled:
    - vendor-hardware
  disabled:
    - experimental-plugin
  strict: false
```

When `enabled` is non-empty, only those plugins are loaded.
Plugins listed in `disabled` are skipped.
With `strict: true`, discovery, validation, registration, or lifecycle failures raise `PluginError`; otherwise they are recorded as diagnostics and built-in functionality continues.

## Lifecycle

`PluginRegistration` accepts optional `validate`, `activate`, and `deactivate` callbacks.
Callbacks receive a `PluginContext` containing the resolved configuration and logger.
Use `validate` for dependency checks that require the local machine, `activate` for starting lightweight resources, and `deactivate` for cleanup.

## Diagnostics

Plugin failures produce domain `Diagnostic` records with stage metadata such as `discovery`, `registration`, `dependency_resolution`, `activation`, or `deactivation`.
Expose actionable causes and avoid leaking secrets from environment variables, credentials, or proprietary tool paths.

See `examples/plugins` for a complete extension example.
