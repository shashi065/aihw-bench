# Example: Plugins

The plugin example shows how to package additional providers without changing AIHW-Bench core code.

Key pieces:

- A `PluginManifest` that declares name, version, plugin API version, package, description, provider kinds, dependencies, and capabilities.
- A `PluginRegistration` that attaches provider objects.
- A `pyproject.toml` entry point under `aihw_bench.plugins`.

Install the example package in editable mode from its directory, then run:

```bash
aihw-bench doctor
```

The doctor command reports plugin registration and compatibility diagnostics.
