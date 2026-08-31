# Reporting System

## Goals

The reporting system turns immutable session data into durable artifacts for humans and automation without changing canonical benchmark records.

## Report Types

### HTML

HTML reports are the primary human-readable format. They include summary tables, chart sections, configuration, hardware metadata, recommendations, and links to raw artifacts.

### Markdown

Markdown reports are optimized for pull requests, GitHub Releases, issues, and research notes.

### CSV

CSV exports are optimized for spreadsheet tools and downstream analysis. Each row preserves metric name, value, unit, source, and comparison keys.

### JSON

JSON reports preserve structured data for automation and long-term archival.

### PDF

PDF support is planned after HTML reports stabilize. PDF rendering will use the same report view model as HTML to avoid duplicated report logic.

### Interactive Reports

Interactive reports use static HTML with embedded or linked Plotly charts. They must remain readable without a live server.

### Future Web Dashboard

The dashboard is a presentation layer over stored sessions. It does not execute benchmark logic directly.

## Report Data Model

Report generation uses a report view model derived from session or comparison data:

- Summary.
- Hardware and system information.
- Configuration.
- Metrics.
- Charts.
- Tables.
- Diagnostics.
- Recommendations.
- Artifact manifest.

Milestone 6 implements the session report view model for benchmark, hardware, model, metric, configuration, diagnostic, and metadata sections. Comparison views and chart-backed report sections remain later milestones.

## Recommendations

Recommendations are policy-driven summaries based on metric thresholds, regressions, missing data, and backend diagnostics. They must state assumptions and must not overclaim hardware conclusions.

## Artifact Policy

Generated reports are written under the session artifact directory or user-selected output directory. Report generation must not modify canonical session files.

## Failure Handling

Report failures are isolated from benchmark measurement. A benchmark can succeed even if one report format fails. The session records report diagnostics.
