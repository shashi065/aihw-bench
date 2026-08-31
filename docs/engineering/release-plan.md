# Release Plan

## Release Channels

- Development snapshots from the main branch.
- Pre-1.0 minor releases for subsystem milestones.
- Stable releases starting at `1.0.0`.

## Versioning

The project follows Semantic Versioning.

- `0.x`: public APIs may change with changelog notes.
- `1.x`: public APIs and CLI behavior are stable within a major version.
- Patch releases contain bug fixes, documentation corrections, and compatible dependency updates.

## Release Checklist

- CI green on all required jobs.
- Changelog updated.
- Documentation builds with `mkdocs build --strict`.
- Package builds as wheel and source distribution.
- SBOM and checksums generated.
- Security scans completed.
- Installation verified on Windows, Ubuntu, and macOS.
- Version is tagged.
- GitHub Release includes release notes and artifacts.
- TestPyPI and PyPI publishing use trusted publishing.
- Docker image build and push complete when registry credentials are configured.
- GitHub Pages documentation deployed.

## GitHub Actions

Required workflows:

- `ci.yml`: lint, format check, type check, tests, coverage.
- `docs.yml`: documentation build and GitHub Pages publish.
- `package.yml`: source distribution and wheel build.
- `release.yml`: full tagged release pipeline for quality gates, artifacts, SBOM, security scans, GitHub Releases, TestPyPI, PyPI, Docker, docs, and cross-platform install verification.

See [Release Engineering](release-engineering.md) for the operational workflow, repository settings, trusted publishing configuration, and maintainer commands.

## Release Artifacts

- Wheel.
- Source distribution.
- HTML documentation site.
- Changelog entry.
- GitHub release notes.
- Coverage report.
- SBOM.
- SHA-256 checksums.

See [Unified Release and Distribution Strategy](distribution-strategy.md) for the complete multi-platform release policy.
