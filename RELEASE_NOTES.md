# AIHW-Bench v2.0.0 Release Notes

Release date: 2026-08-31

AIHW-Bench v2.0.0 completes the feature roadmap with a local benchmark analysis assistant, enterprise foundations, a static dashboard, an official reproducible benchmark suite, and expanded hardware capability reporting.

## Highlights

- Deterministic local benchmark analysis assistant for result explanations, comparisons, anomaly findings, and recommendations. It is not an LLM-backed service.
- Static dashboard with bounded history rendering, filtering, exports, hardware comparison, and report inspection.
- Official-suite contracts use deterministic synthetic manifests and reference fixtures; they are not universal real-device performance claims.
- Vendor/runtime-aware hardware capability reporting for CPU, GPU, embedded, FPGA placeholder, and RTL metadata.
- Local enterprise foundations for workspaces, history indexing, configuration, artifact cataloguing, scheduling models, marketplace metadata, and remote-execution contracts.

## Quality Status

Release validation requires tests and coverage, Ruff, Black, mypy, strict MkDocs, wheel/source build validation, package-asset checks, and version consistency checks.

## Upgrade Notes

Existing public Python and CLI APIs remain supported. Read the current hardware, dashboard, assistant, and official-suite documentation before relying on optional runtime or hardware capabilities.
