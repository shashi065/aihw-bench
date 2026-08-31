# Version Roadmap

## 1.0.0

Stable public release.

Exit criteria:

- Stable public API and CLI.
- Full documentation site.
- Coverage target achieved.
- Release automation complete.
- PyPI publication ready.
- Docker image build verified.
- Release notes, migration guide, final audit, and public roadmap complete.

Status: complete.

## 1.1

Production hardening release.

Planned scope:

- Backend conformance tests and templates for third-party backend authors.
- Additional deterministic sample workloads and benchmark fixture packs.
- Expanded hardware metadata collection for common CPU/GPU hosts.
- Improved multi-session report templates.
- Additional plugin examples for metrics, visualizations, and exporters.
- User instructions for verifying release attestations and signatures.
- Docker image size and layer optimization.

Compatibility policy:

- No breaking public API changes.
- No plugin API version replacement.
- No heavyweight runtime dependencies in the base install.

## Future

Future releases may add simulator and embedded execution plugins, downstream packaging for Conda-Forge and Homebrew, dashboard surfaces built on the existing visualization layer, and native package-manager manifests for Winget, Chocolatey, AUR, and Nixpkgs.
