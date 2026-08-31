# Visualization

Milestone 7 adds deterministic chart specifications and static chart artifact export for benchmark sessions.

## Scope

The visualization layer builds dashboard-ready chart components from stored session data. It does not execute benchmarks and does not implement the future dashboard application.

## Built-in Chart Families

| Family | Purpose |
| --- | --- |
| `latency` | Per-measurement latency over iteration order. |
| `throughput` | Iteration and sample throughput summary. |
| `memory` | Mean and maximum memory usage from metric records. |
| `hardware` | Hardware context such as memory bytes, GPU count, and accelerator count. |
| `timeline` | Run duration timeline across warmup and measurement executions. |
| `performance` | Compact latency, throughput, and estimated FLOPS comparison view. |
| `roofline` | Foundation chart using estimated FLOPS and memory bytes when available. |

## Chart Specifications

`ChartSpec` is the stable visualization contract. It contains a chart ID, title, family, axis labels, traces, and metadata. Traces use a Plotly-compatible shape so reports and future dashboard components can share the same data model.

## Export Formats

`ChartExportService` exports charts to:

- HTML: interactive Plotly-compatible fragment.
- SVG: deterministic static fallback for documents.
- PNG: lightweight preview artifact for pipelines that require bitmap files.

Every exported chart receives checksum metadata.

## Reporting Integration

The default report service embeds dashboard-ready chart components into JSON and HTML reports. Markdown reports list generated chart sections by family and title. CSV remains metric-row focused.

## Boundaries

Milestone 7 does not include a live dashboard server, cross-session comparison service, or advanced interactive exploration. Those remain future milestones.
