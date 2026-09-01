# Release Engineering

Milestone 12 implements the release automation needed to publish AIHW-Bench from a single semantic version tag.

## Release Trigger

Stable releases are tag-driven:

```bash
python scripts/prepare_release.py --version 1.0.0 --date 2026-07-29
git add pyproject.toml CHANGELOG.md
git commit -m "Prepare release 1.0.0"
git tag v1.0.0
git push origin main
git push origin v1.0.0
```

The release workflow validates that:

- The tag uses `vMAJOR.MINOR.PATCH` semantic version format.
- `pyproject.toml` contains the same version without the `v` prefix.
- `CHANGELOG.md` contains a section for the release version.
- The version is not the bootstrap placeholder `0.0.0`.

## Workflows

| Workflow | Purpose |
| --- | --- |
| `ci.yml` | Pull request and main-branch quality gate with coverage artifacts. |
| `package.yml` | Wheel and source distribution build verification. |
| `docs.yml` | Strict MkDocs build and GitHub Pages deployment from main. |
| `release.yml` | Full tag-driven release pipeline. |

## Release Pipeline

`release.yml` performs these stages:

1. Validate release metadata.
2. Run Ruff, Black, mypy, pytest with coverage, `pip-audit`, and strict MkDocs.
3. Build wheel and source distribution.
4. Validate package metadata with Twine.
5. Generate CycloneDX SBOM.
6. Generate release notes from `CHANGELOG.md`.
7. Generate SHA-256 checksums.
8. Sign release assets using Sigstore keyless signing.
9. Verify wheel installation on Ubuntu, Windows, and macOS.
10. Build and push Docker images with provenance and image SBOM enabled.
11. Publish to TestPyPI using trusted publishing.
12. Publish to PyPI using trusted publishing.
13. Create a GitHub Release with signed assets.
14. Deploy documentation to GitHub Pages.

## Trusted Publishing

Configure trusted publishing in PyPI and TestPyPI for:

- Repository: `shashi065/aihw-bench`
- Workflow: `release.yml`
- Environments: `pypi` and `testpypi`

The workflow uses `id-token: write` and does not require PyPI API tokens.

## Signed Releases

Release assets are signed with Sigstore keyless signing. The workflow requests an OIDC token and uploads the generated signature bundles alongside the wheel, source distribution, SBOM, checksums, release notes, changelog, and license.

## Docker Publishing

The workflow always publishes to GitHub Container Registry:

```text
ghcr.io/<owner>/aihw-bench:<tag>
ghcr.io/<owner>/aihw-bench:<version>
ghcr.io/<owner>/aihw-bench:latest
```

Docker Hub publishing is enabled by setting:

- Repository variable `DOCKERHUB_IMAGE`, for example `aihwbench/aihw-bench`.
- Secret `DOCKERHUB_USERNAME`.
- Secret `DOCKERHUB_TOKEN`.

The Dockerfile uses a builder stage to build and install the wheel into a dedicated virtual environment, then copies that environment into the runtime image. The build stage and runtime stage both smoke-check `aihw-bench version` so packaging or entry point failures stop the image before it is published.

Local validation:

```bash
docker build -t aihw-bench:local .
docker run --rm aihw-bench:local version
docker run --rm aihw-bench:local doctor
```

On Windows hosts, ensure Docker Desktop's `resources/bin` directory is on the shell PATH so `docker-credential-desktop` can be found during BuildKit pulls. See [Troubleshooting](../user-guide/troubleshooting.md) for the PowerShell and WSL commands.

## Release Readiness

Before tagging, run:

```bash
python scripts/check_release_version.py --tag v1.0.0
python -m build
python -m twine check dist/*
python -m pytest
python -m mkdocs build --strict
```

The repository bootstrap version `0.0.0` intentionally fails release validation. Stable releases must use a real semantic version such as `1.0.0`.
