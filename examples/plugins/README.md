# Plugin Examples

Plugin examples show how third-party packages extend AIHW-Bench through the `aihw_bench.plugins` entry point group.

Included examples:

- `example_plugin.py`: registers metric, report, visualization, CLI command, and exporter providers.
- `pyproject.toml`: shows the entry point declaration for an installable plugin package.

Rules for examples:

- Declare a supported plugin API version.
- Avoid vendor SDKs or private hardware requirements.
- Keep provider behavior deterministic enough for conformance tests.
