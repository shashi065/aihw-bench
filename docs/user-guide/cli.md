# Command Line Interface

Milestone 8 provides the primary `aihw-bench` command surface for local benchmark workflows.

## Commands

| Command | Purpose |
| --- | --- |
| `benchmark` | Run a benchmark, persist the session, and generate configured reports. |
| `profile` | Run a benchmark with profiler names recorded in configuration. |
| `compare` | Compare one metric between two stored sessions. |
| `report` | Generate reports for an existing stored session. |
| `export` | Export canonical session JSON and optional report formats. |
| `config` | Resolve configuration from defaults, files, environment, and CLI overrides. |
| `doctor` | Check runtime health, core dependencies, and plugin validity. |
| `version` | Print package, Python, platform, plugin API, and dependency versions. |

Typer provides shell completion through:

```bash
aihw-bench --install-completion
```

## Benchmark

```bash
aihw-bench benchmark \
  --config examples/configs/reference-benchmark.yaml \
  --storage-root .aihw-bench/sessions \
  --output-dir reports \
  --report json \
  --report html
```

The command shows a Rich progress indicator while the benchmark service runs. Results are stored as immutable sessions, and configured reports are generated after measured execution completes.

## Compare

```bash
aihw-bench compare baseline-session candidate-session --metric latency_mean_seconds
```

Use `--output json` for automation.

## Report And Export

```bash
aihw-bench report SESSION_ID --format markdown --format html
aihw-bench export SESSION_ID --format csv --format json
```

`report` creates human and machine-readable report artifacts. `export` always writes canonical session JSON and can additionally generate report-format exports.

## Config

```bash
aihw-bench config --config examples/configs/reference-benchmark.yaml --output table
```

The config command is useful in CI because it shows the final resolved configuration after defaults, file settings, environment variables, and CLI overrides have been merged.

## Error Handling

Expected failures print a concise message, cause, suggested fix, and documentation link when available. CLI exit codes follow the engineering CLI specification.
