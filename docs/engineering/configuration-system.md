# Configuration System

## Goals

The configuration system provides deterministic benchmark setup across local CLI usage, CI jobs, lab machines, and plugin-driven workflows.

## Supported Sources

Configuration is resolved from:

1. CLI options.
2. Environment variables.
3. Configuration file.
4. Defaults.

Higher-priority sources override lower-priority sources.

## File Formats

YAML and JSON are supported. YAML is preferred for human-authored configuration. JSON is preferred for generated or machine-managed configuration.

## Environment Variables

Environment variables use a single project prefix:

```text
AIHW_BENCH_
```

Nested keys use double underscores. For example, `AIHW_BENCH_EXECUTION__ITERATIONS` maps to `execution.iterations`.

## Configuration Profiles

Profiles allow reuse of common settings:

- `default`
- `ci`
- `quick`
- `accurate`
- `embedded`
- `simulator`
- user-defined profiles

Profiles may inherit from another profile. Cyclic inheritance is invalid.

## Defaults

Defaults must be conservative:

- Small iteration counts for initial usability.
- Explicit warmup behavior.
- Local filesystem session store.
- No optional heavy profiler unless requested.
- No network access unless a configured integration requires it.

## Validation

Validation occurs before execution. Invalid configuration fails fast and includes:

- Invalid key path.
- Invalid value.
- Expected type or range.
- Suggested correction.
- Documentation link.

## Security

The configuration loader rejects unsafe paths, path traversal, unsupported formats, and unknown keys in strict mode. It does not evaluate arbitrary code.

## Resolved Configuration Artifact

Every benchmark session stores `config.resolved.yaml`. This file captures the effective configuration after all precedence and inheritance rules are applied.

## Future Extensions

- Organization-level shared profiles.
- Remote configuration sources.
- Signed configuration bundles.
- Encrypted secret references for remote hardware labs.
