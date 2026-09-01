# Unified Release and Distribution Strategy

## Objective

AIHW-Bench releases are driven by a single semantic-version Git tag. A maintainer pushes a tag such as `v1.0.0`, and automation performs validation, builds artifacts, publishes release assets, deploys documentation, and verifies installation across supported operating systems.

Manual packaging is not part of the release process.

## Release Targets

### Primary

- GitHub Releases.
- PyPI.
- TestPyPI.
- GitHub Pages documentation.

### Secondary

- Conda-Forge.
- Docker Hub.
- Homebrew tap for the CLI.
- Dev Container image.

### Future

- Snapcraft.
- Winget.
- Chocolatey.
- Arch User Repository.
- Nixpkgs.

## Tag-Driven Pipeline

The `release.yml` workflow runs on tags matching `v*.*.*`.

Required release jobs:

1. Validate tag and package version alignment.
2. Run Ruff.
3. Run Black.
4. Run mypy.
5. Run pytest.
6. Measure coverage.
7. Build documentation.
8. Generate API documentation through MkDocs and mkdocstrings.
9. Build Python wheel.
10. Build source distribution.
11. Generate SBOM.
12. Run security scans.
13. Sign release artifacts with Sigstore keyless signing.
14. Verify wheel installation on Windows, Ubuntu, and macOS.
15. Publish to TestPyPI using trusted publishing.
16. Publish to PyPI using trusted publishing.
17. Build Docker image.
18. Push Docker image to GHCR and Docker Hub when configured.
19. Create GitHub Release.
20. Upload release assets.
21. Deploy GitHub Pages.
22. Generate release notes from the changelog and Git history.
23. Verify changelog entry for the release version.
24. Publish package metadata through registry-native mechanisms.

## Version Policy

AIHW-Bench follows Semantic Versioning.

- Tags use the format `vMAJOR.MINOR.PATCH`.
- Package metadata uses `MAJOR.MINOR.PATCH`.
- The release workflow fails if the tag and package metadata differ.
- The changelog must include a section for the release version before the tag is pushed.
- `project.version` must be moved away from `0.0.0` before a publishable release tag is accepted.

## Artifact Requirements

Every release includes:

- Python wheel.
- Source distribution.
- SHA-256 checksums.
- Release notes.
- Changelog.
- License.
- SBOM.
- Coverage report.
- Documentation site.

## Publishing Policy

PyPI and TestPyPI use trusted publishing through GitHub Actions OIDC. Docker publishing always targets GitHub Container Registry and also targets Docker Hub when `DOCKERHUB_IMAGE`, `DOCKERHUB_USERNAME`, and `DOCKERHUB_TOKEN` are configured. GitHub Releases and GitHub Pages use workflow-scoped GitHub Actions permissions.

Conda-Forge, Homebrew, and future package managers are downstream ecosystems. The project maintains packaging metadata and documentation for those channels, but ecosystem-specific publication may occur through their normal review processes.

## Installation Validation

Before release publication completes, automation verifies:

- `pip install` from the built wheel.
- `python -c "import aihw_bench"`.
- `aihw-bench version`.
- `aihw-bench doctor`.
- Documentation builds with strict mode.
- Examples execute successfully once example workloads are added.

The verification matrix includes Windows, Ubuntu, and macOS.

## Documentation URL

The canonical documentation URL is:

```text
https://shashi065.github.io/aihw-bench/
```

If the GitHub organization changes, `mkdocs.yml`, repository metadata, package metadata, and release documentation must be updated in the same change.
