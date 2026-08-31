# Roadmap

AI Hardware Benchmark Suite is now at the v1.0 stable release baseline.

The detailed execution plan remains in the [Technical Implementation Roadmap](docs/engineering/technical-implementation-roadmap.md). The public roadmap below focuses on compatible post-1.0 improvements.

## v1.0.0: Stable Release

Status: complete.

- Stable public Python API and CLI.
- Core benchmark execution, metrics, reporting, visualization, plugin, documentation, testing, release, and Docker infrastructure.
- 95%+ coverage gate.
- Trusted publishing-ready release workflow.
- GitHub Pages documentation.
- SBOM, checksums, signed release assets, Docker image publishing, and cross-platform installation verification.

## v1.1: Production Hardening

Planned scope:

- Improve backend conformance test coverage for third-party backend authors.
- Add richer benchmark fixture packs and deterministic sample workloads.
- Expand hardware metadata collection for common CPU/GPU hosts while preserving graceful fallback behavior.
- Improve report templates for long multi-session comparisons.
- Add plugin compatibility examples for metrics, visualizations, and exporters.
- Add release attestation verification instructions for users.
- Improve Docker image size and dependency layering after real-world usage feedback.

Non-goals for v1.1:

- Breaking public API changes.
- Replacing the plugin API version.
- Adding heavyweight runtime dependencies to the base install.

## Future

- Simulator and embedded execution plugins.
- Conda-Forge and Homebrew downstream packaging.
- Dashboard application surface built on existing visualization components.
- Native package-manager manifests for Winget, Chocolatey, AUR, and Nixpkgs.
