# Plugin Architecture Specification

## Goals

Plugins allow users and vendors to add new hardware backends, model runtimes, metrics, report generators, visualizations, profilers, and storage implementations without modifying core code.

## Discovery

Plugins are discovered through the Python entry point group:

```toml
[project.entry-points."aihw_bench.plugins"]
vendor_accelerator = "vendor_package.aihw_plugin:plugin"
```

The entry point target returns a plugin descriptor object.

## Plugin Descriptor

Required metadata:

- `name`
- `version`
- `api_version`
- `description`
- `providers`

Provider types:

- `backend`
- `profiler`
- `metric`
- `reporter`
- `visualizer`
- `session_store`
- `hardware_inspector`

## Validation

The plugin loader validates:

- Descriptor schema.
- Supported plugin API version.
- Unique provider names.
- Required provider capabilities.
- Optional dependency availability.

Plugin load failures are reported through `doctor` and structured logs. A failed plugin must not prevent unrelated built-in functionality from loading.

## Isolation

Plugins run in-process for the initial release. The API keeps subprocess or remote-plugin isolation possible for future high-risk integrations, especially simulator and vendor SDK integrations.

## Compatibility

Plugin API versions follow the core package minor version until `1.0.0`. After `1.0.0`, incompatible plugin API changes require a major version.

## Documentation Requirements for Plugins

Third-party plugin packages should document:

- Supported hardware or runtime versions.
- Required external tools.
- Configuration schema.
- Metrics and units.
- Known measurement limitations.
- Reproducibility notes.
