# Changelog

All notable changes to AI Hardware Benchmark Suite will be documented in this file.

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-08-31

### Added

- Added a grounded, local-first benchmark assistant for explanations, hardware comparisons, optimization recommendations, anomaly detection, summaries, Markdown reports, and recommended configurations.
- Added CLI and dashboard assistant integrations plus an optional AI-provider extension protocol.


## [1.5.0] - 2026-08-31

### Added

- Added enterprise foundations for workspace profiles, project configurations, a local plugin marketplace index, transport-neutral remote execution, pollable schedules, SQLite benchmark history, result comparisons, and artifact catalog integration.


## [1.4.0] - 2026-08-31

### Added

- Added a responsive static dashboard with history, hardware comparison, interactive charts, report browsing, search/filtering, JSON/CSV export, and dark mode.


## [1.3.0] - 2026-08-31

### Added

- Added the official reproducible suite for image classification, detection, segmentation, LLMs, Vision Transformers, CNNs, audio, speech, embedded AI, and TinyML.
- Added deterministic dataset manifests, reference baseline results, public API, CLI commands, and benchmark-by-benchmark documentation.


## [1.2.0] - 2026-08-31

### Added

- Added vendor-neutral detection and capability reporting for Intel, AMD, and Apple CPUs; CUDA, ROCm, and Intel GPUs; Raspberry Pi, Jetson, Coral, FPGA placeholders, and RTL simulator metadata.
- Added RTL simulator and FPGA placeholder backends.
- Added advanced hardware support documentation.


## [1.1.0] - 2026-08-31

### Changed

- Reused one materialized report view for multi-format report generation.
- Compiled the invariant HTML report template once per process.
- Reused benchmark statistics during metric derivation and collected observations in one pass.
- Cached static host detection per hardware-inspector instance while preserving dynamic policy environment values.
- Reduced bulk plugin registration list churn during dependency resolution.
- Added deterministic v1.1 performance comparisons and profile results.


## [1.0.1] - 2026-08-31

### Changed

- Removed unused runtime dependencies from the PyPI and Conda package metadata.
- Deduplicated requested report and chart export formats while preserving request order.
- Added v1.0.1 refactoring, technical-debt, performance, and security audit reports.

### Fixed

- Prevented non-positive SHA-256 chunk sizes from entering a non-advancing read loop.
- Escaped public chart text in generated HTML and SVG, including inline chart data.
- Corrected a stale SHA-256 test expectation.


## [1.0.0] - 2026-07-29

### Added

- Shipped the stable AIHW-Bench 1.0 repository with repository foundation, core infrastructure, benchmark engine, model support, hardware backends, metrics, reporting, visualization, CLI, plugin framework, testing and QA, documentation, release engineering, and final release readiness.
- Added a stable public Python package surface through `aihw_bench.__all__`.
- Added the Typer/Rich CLI commands `benchmark`, `profile`, `compare`, `report`, `export`, `config`, `doctor`, `completion`, and `version`.
- Added immutable Pydantic domain models for configurations, sessions, execution records, benchmark results, metrics, profiles, diagnostics, hardware profiles, model metadata, plugins, run history, and export artifacts.
- Added configuration loading with defaults, YAML/JSON files, profiles, environment variables, CLI overrides, validation, and source explanation.
- Added benchmark execution lifecycle management with scheduling, warmup and measured iterations, retry handling, timeout handling, partial-session recovery, statistics, session persistence, metrics integration, and report hooks.
- Added built-in reference, CPU, and GPU backend support with backend registry selection, validation, hardware capability detection, and hardware information collection.
- Added model loading support for PyTorch/TorchScript, ONNX Runtime, and TensorFlow Lite through optional runtime adapters.
- Added latency, throughput, memory, CPU/GPU utilization, FLOPS estimate, statistical aggregation, result serialization, benchmark summary, and reporting integration.
- Added JSON, CSV, Markdown, and HTML reporting with report metadata, export directory management, validation, and visualization integration.
- Added chart abstractions, latency, throughput, memory, timeline, hardware comparison, performance comparison, and roofline foundation visualizations with HTML, SVG, and PNG export support.
- Added plugin discovery, registration, validation, API compatibility checks, dependency resolution, lifecycle callbacks, error isolation, configuration, and extension examples.
- Added professional MkDocs documentation with API reference, beginner guide, advanced guide, tutorials, examples, plugin guide, developer guide, contributing guide, FAQ, troubleshooting, release engineering, and final release audit.
- Added CI, packaging, documentation, and release workflows for quality gates, wheel/source distribution builds, SBOM generation, signed release artifacts, GitHub Releases, TestPyPI/PyPI trusted publishing, Docker image publishing, and GitHub Pages deployment.
- Added Docker image support with a multi-stage wheel build, non-root runtime user, and build-time CLI smoke checks.
- Added unit, integration, CLI, regression, performance, release engineering, and Dockerfile tests with coverage enforcement above 95%.

### Changed

- Promoted package metadata to production/stable status for the 1.0.0 release.
- Updated public README, roadmap, release documentation, and troubleshooting content to describe the stable 1.0 release state.
- Updated release validation so `project.version`, runtime `__version__`, changelog, and semantic release tags must match.

### Security

- Verified expected security posture for 1.0.0: typed domain errors for expected failures, secret redaction in logging, path containment helpers, plugin error isolation, strict release gates, trusted publishing, Sigstore-signed release assets, SBOM generation, Docker build provenance, and dependency audit workflow integration.

## [0.0.0] - 2026-07-29

### Added

- Established repository governance, packaging metadata, documentation skeleton, and engineering design baseline.
- Added architecture, API, plugin, CLI, testing, release, and roadmap specifications for phased implementation.
- Added the project constitution and open-source contribution templates.
- Added unified release and distribution strategy covering GitHub Releases, PyPI, TestPyPI, GitHub Pages, Docker, Conda-Forge, Homebrew, and future package ecosystems.
- Added complete PRD and expanded architecture documentation for module design, data models, configuration, benchmark engine, reporting, visualization, security, performance, coding standards, and contribution standards.
- Replaced the initial SRS with an IEEE-style requirements specification containing requirement IDs, priorities, acceptance criteria, interface requirements, data requirements, security requirements, release requirements, and a traceability matrix.
- Replaced the initial SDD with a complete software design blueprint covering architecture, subsystems, class designs, interfaces, plugins, data models, workflows, configuration, error handling, performance, security, testability, observability, release engineering, documentation, and implementation milestones.
- Added a mandatory Engineering Handbook defining repository standards, coding standards, documentation standards, testing standards, Git workflow, versioning, CI/CD, security, performance, release engineering, quality gates, open-source governance, engineering decision process, and long-term maintenance policy.
- Added the Technical Implementation Roadmap defining Milestones 0 through 13, critical path, parallel work opportunities, risk register, dependency graph, release timeline, quality gates, and roadmap governance.
