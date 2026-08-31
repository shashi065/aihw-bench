# Reporting

Milestone 6 adds a static reporting engine for immutable benchmark sessions.

## Report Flow

`ReportService` validates a finalized `BenchmarkSession`, builds one canonical `ReportView`, and delegates rendering to a registered reporter. Built-in reporters generate JSON, CSV, Markdown, and standalone HTML artifacts.

Report generation runs after measurement and does not mutate canonical session files. If the benchmark service is configured with a report service, report failures are logged and isolated from benchmark execution.

## Built-in Formats

| Format | Extension | Purpose |
| --- | --- | --- |
| JSON | `.json` | Structured automation export with metadata, summaries, metrics, configuration, and diagnostics. |
| CSV | `.csv` | One row per metric for spreadsheets and downstream analysis. |
| Markdown | `.md` | Pull requests, issues, release notes, and research notes. |
| HTML | `.html` | Static human-readable report with benchmark, metric, hardware, model, and diagnostic sections. |

## Report Sections

Every built-in report is derived from the same view model:

- Report metadata: report ID, session ID, format, generator, version, and generation timestamp.
- Benchmark summary: status, backend, device, precision, batch size, measurement count, and primary metrics.
- Hardware summary: host, CPU, memory, GPU, accelerators, drivers, thermal policy, and power policy.
- Model summary: model ID, name, format, and precision when workload metadata is available.
- Metrics: all primary and secondary metrics with units, kind, source, assumptions, and comparison direction.
- Charts: dashboard-ready chart specifications and HTML components when visualization is enabled.
- Configuration: resolved benchmark configuration.
- Diagnostics: warnings and errors captured during execution.

## CLI

```bash
aihw-bench report SESSION_ID --storage-root .aihw-bench/sessions --output-dir reports --format json --format markdown
```

When no `--format` option is supplied, the command uses `reports.formats` from the stored session configuration.

## Validation

Reports require finalized sessions. Unsupported formats raise structured `ReportError` exceptions with documentation links and suggestions. Output directories are created automatically and generated artifacts include SHA-256 checksums.
