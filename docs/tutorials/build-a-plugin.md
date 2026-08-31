# Tutorial: Build A Plugin

This tutorial mirrors the extension pattern in `examples/plugins`.

## 1. Define A Manifest

```python
from aihw_bench.application import PluginManifest, PluginProviderKind

manifest = PluginManifest(
    name="example",
    version="0.1.0",
    api_version="1.0",
    package="aihw-bench-example-plugin",
    description="Example AIHW-Bench extension.",
    providers=(PluginProviderKind.METRICS,),
)
```

## 2. Return A Registration

```python
from aihw_bench.application import PluginRegistration


def register_plugin() -> PluginRegistration:
    return PluginRegistration.from_manifest(
        manifest,
        providers={"metrics": {"example": ExampleMetricProvider()}},
    )
```

## 3. Expose An Entry Point

```toml
[project.entry-points."aihw_bench.plugins"]
example = "aihw_bench_example_plugin:register_plugin"
```

## 4. Validate Locally

```bash
aihw-bench doctor
```

If the plugin is incompatible, missing a dependency, or returns an unsupported object, the plugin framework records a diagnostic. With strict mode enabled, those failures raise `PluginError`.
