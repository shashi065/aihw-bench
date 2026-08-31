# v1.0.0 Release Audit

Audit date: 2026-07-29

## Scope

This audit covers the final repository readiness state for AIHW-Bench v1.0.0. It does not introduce new features; it verifies that implemented Milestones 0-12 are coherent, documented, tested, and releasable.

## Repository Audit

- Package metadata is set to `1.0.0`.
- Runtime `aihw_bench.__version__` is set to `1.0.0`.
- Changelog contains a dated `1.0.0` section.
- Release notes and migration guide are present at the repository root.
- MkDocs navigation includes user guides, developer guides, examples, API reference, release engineering, and this audit.
- Dockerfile builds a wheel before runtime installation and smoke-checks the CLI.

## API Stability Verification

The stable public API is exported from `aihw_bench.__all__`. The public surface includes benchmark requests and outcomes, benchmark service orchestration, timing engines, domain models, domain protocols, model-loading contracts, plugin framework types, and core runtime errors.

Stability policy for v1.x:

- Public package exports require backwards-compatible behavior within the major version.
- CLI command names and documented options require backwards-compatible behavior within the major version.
- Plugin API version remains `1.0` until a future explicitly versioned plugin contract is introduced.

## Performance Validation

The deterministic performance test suite validates framework overhead with fake backends and scripted timing. Host-specific performance claims are intentionally not encoded in unit tests because they depend on CPU, GPU, driver, and runtime conditions.

Release validation requires:

- deterministic performance tests pass;
- benchmark execution does not require specific host hardware;
- Docker image build completes and CLI startup works inside the runtime image.

## Security Audit

Security posture for v1.0.0:

- Expected failures use typed domain errors with causes, suggestions, and documentation links.
- Logging redacts common token, password, secret, and API key assignments.
- Filesystem helpers constrain paths inside configured roots.
- Plugin discovery and lifecycle failures are isolated as diagnostics unless strict mode is enabled.
- Release workflow uses trusted publishing for PyPI and TestPyPI.
- Release workflow generates SBOMs, checksums, and Sigstore keyless signatures.
- Docker release workflow enables image provenance and image SBOM generation.

Local audit result:

- A clean temporary virtual environment was created.
- The v1.0.0 wheel was installed into that environment.
- `pip-audit` reported no known vulnerabilities for the release dependency environment.
- The local unpublished `aihw-bench` wheel was skipped by `pip-audit` because it is not yet available on PyPI.

## Dependency Review

The base dependency set remains intentionally small and excludes heavyweight model runtimes. PyTorch, ONNX Runtime, and TensorFlow Lite are optional extras or runtime-specific dependencies.

Base dependencies:

- Jinja2
- NumPy
- pandas
- Plotly
- Pydantic
- pydantic-settings
- PyYAML
- Rich
- Typer

Dependency policy for v1.x:

- Keep heavy accelerator runtimes optional.
- Prefer compatible lower bounds until real-world compatibility data justifies upper bounds.
- Continue running `pip-audit` in release workflow security gates.
- Review dependency changes in changelog entries.

## Documentation Audit

The documentation site includes API reference, user guides, CLI guide, tutorials, examples, plugin guide, developer guide, contributing guide, FAQ, troubleshooting, release engineering, migration guide, and public roadmap.

Documentation validation uses `mkdocs build --strict`.

## Release Candidate Status

The repository is ready to produce the `v1.0.0` release candidate after local gates pass and maintainers confirm PyPI/TestPyPI trusted publishing environments.

Release command:

```bash
git tag v1.0.0
git push origin v1.0.0
```
