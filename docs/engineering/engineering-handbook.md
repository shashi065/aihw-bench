# Engineering Handbook

Document status: Mandatory standard  
Applies to: All AIHW-Bench contributors, maintainers, releases, plugins, documentation, and automation  
Authority order: Project Constitution -> SRS -> SDD -> Engineering Handbook -> ADRs -> subsystem docs

## 1. Engineering Philosophy

AIHW-Bench is built as long-lived open-source infrastructure. Every engineering decision must support correctness, reproducibility, maintainability, and trustworthy benchmark results.

### Core Principles

- Correctness over shortcuts.
- Maintainability over cleverness.
- Readability over accidental complexity.
- Performance with evidence.
- Stable APIs by default.
- Documentation-first for public behavior.
- Testing-first for feature work.
- Open-source first in process and artifacts.
- Reproducibility as a product feature.
- Backward compatibility whenever practical.

### Practical Interpretation

- A fast benchmark result is not useful if it cannot be reproduced.
- A clever abstraction is not acceptable unless it reduces real complexity.
- A public API is a promise and must be versioned.
- A feature is not complete until docs, tests, diagnostics, packaging, and release impact are handled.
- Optional hardware and runtime dependencies must not make the core package fragile.

## 2. Repository Standards

### Folder Naming

Folders use lowercase names. Python packages use lowercase snake_case. Documentation folders use lowercase kebab-case where they are URL-facing.

Required top-level folders:

- `.github`: workflows, issue templates, pull request templates.
- `.devcontainer`: development container configuration.
- `docs`: documentation source.
- `packaging`: downstream package metadata.
- `scripts`: maintainer and release helper scripts.
- `src`: Python package source.
- `tests`: test suite.
- `examples`: future example configurations, reports, and plugins.

### File Naming

- Python files use `snake_case.py`.
- Markdown files use lowercase kebab-case.
- Workflow files use descriptive lowercase names.
- Generated files are not committed unless they are intended release artifacts or documentation source.

### Module Naming

Module names describe responsibility, not implementation detail. A module should answer one question: "What concept does this own?"

Acceptable examples:

- `configuration_loader`
- `session_store`
- `metric_provider`
- `backend_registry`

Unacceptable examples:

- `misc`
- `helpers2`
- `new_stuff`
- `temp`

### Package Naming

The import package is `aihw_bench`. Distribution name is `aihw-bench`. Plugin entry points use `aihw_bench.plugins`.

### Import Rules

Allowed dependency direction:

```text
presentation -> application -> domain
presentation -> infrastructure
infrastructure -> domain
application -> domain
utils -> dependency-neutral helpers
```

Forbidden imports:

- Domain importing infrastructure.
- Domain importing CLI code.
- Application importing presentation code.
- Backends importing unrelated backends.
- Visualization importing benchmark execution services.

### Dependency Rules

- Core dependencies must be lightweight and portable.
- Heavy runtime dependencies belong in extras or plugins.
- Vendor SDKs, simulator binaries, and hardware-specific tools are never required for core installation.
- New dependencies require justification, license review, maintenance review, and security review.

### Repository Organization

Repository organization must match documented architecture. New folders require a clear owner, purpose, and documentation update.

## 3. Coding Standards

### Python Version

AIHW-Bench targets Python 3.12+. Support windows are documented in the release policy.

### Typing

- Strict typing is mandatory.
- Public APIs must be fully typed.
- `Any` is allowed only for validated dynamic metadata or interoperability boundaries.
- Type ignores require a justification comment.

### Docstrings

- Public classes, public methods, public functions, and public modules use Google-style docstrings.
- Docstrings describe purpose, arguments, returns, raised exceptions, and examples when public.

### Naming Conventions

- Classes use `PascalCase`.
- Functions, methods, variables, and modules use `snake_case`.
- Constants use `UPPER_SNAKE_CASE`.
- Exceptions end with `Error`.
- Protocols and interfaces describe role, such as `BenchmarkBackend` or `MetricProvider`.

### Function Size

Functions should usually stay under 40 logical lines. Longer functions require clear justification and should be split when multiple responsibilities appear.

### Class Size

Classes should usually stay under 250 logical lines. Large classes must be split by responsibility unless they are intentionally simple data models.

### File Size

Files should usually stay under 500 logical lines. Larger files require a module-splitting review.

### Comments

Comments explain why, not what. Prefer clear naming over explanatory comments. Complex algorithmic or benchmarking assumptions must be documented near the logic and in public docs when user-visible.

### Logging

- Logs are structured where practical.
- Logs include session ID, phase, provider, and diagnostic code when relevant.
- Logs must not expose secrets.
- CLI output is not a substitute for logs.

### Exceptions

Expected exceptions are classified by subsystem:

- Configuration.
- Validation.
- Backend.
- Runtime.
- Profiler.
- Metric.
- Plugin.
- Storage.
- Report.
- Export.
- Security.
- Internal.

Every expected error should include cause, suggested solution, and documentation reference where practical.

### Constants

Constants live near their owning subsystem. Shared constants require ownership documentation. Configuration values are not hardcoded as constants when users reasonably need to change them.

### Configuration

Configuration is loaded through the configuration manager only. Business logic receives resolved configuration and does not read environment variables or files directly.

### Dependency Injection

Application services receive collaborators through constructors or explicit composition roots. Benchmark code must be testable with fake clocks, fake stores, fake backends, fake profilers, and fake reporters.

## 4. Documentation Standards

Documentation is product work. A feature without documentation is incomplete.

### Module Documentation

Every module must document its responsibility, public contracts, ownership boundary, and relevant architecture links.

### Public API Documentation

Every public API must include:

- Purpose.
- Inputs.
- Outputs.
- Exceptions.
- Example.
- Version history when behavior changes.
- Deprecation notice when applicable.

### CLI Documentation

Every CLI command must include:

- Usage.
- Arguments.
- Options.
- Examples.
- Expected output.
- Exit codes.
- Common errors.
- Related configuration keys.

### Documentation Quality Rules

- Documentation must build in strict mode.
- Broken links block merge.
- Architecture diagrams must remain current when architecture changes.
- Examples must be runnable once implementation exists.
- Reports, exports, and configuration schemas must be documented before release.

## 5. Testing Standards

Every feature requires tests appropriate to risk and blast radius.

### Unit Tests

Unit tests cover domain policies, validators, metrics, configuration merging, error classification, and isolated helpers.

### Integration Tests

Integration tests cover real subsystem collaboration, including configuration to benchmark service, session persistence, report generation, plugin loading, and export.

### Regression Tests

Regression tests are required for every bug fix that can reasonably recur.

### CLI Tests

CLI tests validate help text, exit codes, output modes, invalid input, common errors, and machine-readable output.

### Performance Tests

Performance tests are required for benchmark engine changes, metrics aggregation changes, storage changes, report generation changes, and large-session handling.

### Coverage Thresholds

The project target is at least 90% coverage by `1.0.0`. Coverage decreases require maintainer approval and documented rationale.

### Benchmark Validation

Benchmark validation tests must verify that framework overhead is separated from workload timing where practical and that warmup data does not contaminate primary metrics.

## 6. Git Workflow

### Branch Strategy

- `main` is always releasable.
- Feature branches are short-lived and focused.
- Release branches may be used for stabilization.
- Hotfix branches target supported release lines.

### Commit Message Format

Commit messages should be concise and action-oriented:

```text
area: describe the change
```

Examples:

- `docs: add benchmark lifecycle SRS requirements`
- `ci: add release artifact checksum generation`
- `config: validate profile inheritance cycles`

### Pull Request Requirements

Every pull request must include:

- Summary.
- Motivation.
- Architecture impact.
- Test evidence.
- Documentation updates.
- Compatibility impact.
- Security impact when relevant.
- Performance impact when relevant.
- Changelog entry for user-facing changes.

### Code Review Process

Reviewers evaluate correctness, architecture boundaries, typing, tests, docs, security, performance, compatibility, and maintainability.

### Merge Policy

No code may merge unless required CI passes, review is complete, docs are updated, and quality gates are satisfied.

### Release Branches

Release branches are used only when needed for stabilization or backports. Release branches must receive only targeted fixes.

### Hotfixes

Hotfixes require issue linkage, regression coverage, changelog entry, and patch release planning.

## 7. Versioning

### Semantic Versioning

AIHW-Bench follows Semantic Versioning.

```text
MAJOR.MINOR.PATCH
```

Tags use:

```text
vMAJOR.MINOR.PATCH
```

### Development Releases

Development releases may be used for early integration testing. They are not stable API commitments.

### Alpha

Alpha releases validate architecture, APIs, and early backends. Breaking changes may occur with changelog notes.

### Beta

Beta releases indicate feature completeness for a milestone. Breaking changes require stronger justification and migration notes.

### Release Candidate

Release candidates are stabilization builds. Only bug fixes, docs fixes, packaging fixes, and release fixes are expected.

### Stable

Stable releases preserve public APIs within a major version.

### Deprecation Policy

Deprecations require:

- Warning period.
- Documentation.
- Migration path.
- Changelog entry.
- Removal version.

### Backward Compatibility

Backward compatibility is preferred whenever practical. Breaking changes require maintainer approval, versioning, migration documentation, and release notes.

## 8. CI/CD Standards

Every pull request must run:

- Formatting checks.
- Linting.
- Type checking.
- Security scans.
- Tests.
- Coverage.
- Documentation build.
- Package build.

Required tools:

- Black for formatting.
- Ruff for linting.
- mypy for type checking.
- pytest and pytest-cov for tests and coverage.
- MkDocs strict mode for docs.
- Python build frontend for packaging.
- Dependency audit and SBOM tooling for release.

CI must be fast enough for contributors and strict enough to protect release quality.

## 9. Security

### Dependency Updates

Dependencies are reviewed for maintenance status, license compatibility, vulnerability history, transitive dependency impact, and optionality.

### SBOM Generation

Every release includes an SBOM artifact.

### Secret Scanning

Secrets must not be committed. CI should include secret scanning when available.

### Dependency Scanning

Release and scheduled workflows should audit dependencies.

### Static Analysis

Static analysis is required for security-sensitive code paths, especially configuration, plugins, file handling, and report rendering.

### Signed Releases

The release architecture reserves support for signed releases and provenance attestations.

### Trusted Publishing

PyPI and other registries should use trusted publishing where supported.

## 10. Performance

### Performance Budgets

Budgets are established per subsystem as implementation matures:

- CLI startup should remain responsive.
- Benchmark measured regions should avoid framework overhead.
- Report generation should not run during measured execution.
- Large-session operations should avoid unbounded memory growth.

### Memory Budgets

Memory-sensitive paths must avoid avoidable copies, eager large-file loading, and unbounded in-memory aggregation.

### Profiling Rules

Optimize only after measuring. Performance PRs must state measurement method, baseline, result, and tradeoffs.

### Optimization Policy

Prefer simple, correct implementations until evidence shows a bottleneck. Optimizations must not obscure correctness.

### Benchmark Validation

Benchmark validation must distinguish workload time, framework overhead, backend preparation, warmup, report generation, and storage time.

### Regression Detection

Performance-sensitive subsystems require regression thresholds once stable baselines exist.

## 11. Release Engineering

Every release must automatically publish or prepare:

- GitHub Releases.
- PyPI.
- TestPyPI.
- GitHub Pages.
- Docker Hub or configured container registry.
- Conda-Forge metadata when accepted.

Every release must generate:

- Release notes.
- Changelog.
- SBOM.
- Checksums.
- Documentation.
- API docs.
- Wheel.
- Source distribution.

Release automation must verify installation on Windows, Linux, and macOS before publication.

## 12. Quality Gates

No code may be merged unless:

- Tests pass.
- Coverage meets the current target.
- Formatting passes.
- Linting passes.
- Type checking passes.
- Security checks pass.
- Documentation is updated.
- Changelog is updated for user-facing changes.
- Public API and compatibility impacts are documented.
- Release impact is understood.

Maintainers may require additional gates for security-sensitive, performance-sensitive, packaging, or public API changes.

## 13. Open Source Governance

### Issue Templates

Issue templates collect actionable reproduction steps, environment details, logs, expected behavior, actual behavior, and impact.

### Discussion Rules

Discussions are used for roadmap proposals, plugin ideas, architecture questions, benchmarking methodology, and community support.

### Contribution Rules

Contributors must follow the constitution, SRS, SDD, handbook, and contribution standards.

### Maintainer Responsibilities

Maintainers own:

- Architecture quality.
- Review standards.
- Release integrity.
- Security response.
- Community moderation.
- Roadmap management.
- Compatibility policy.

### Community Standards

The code of conduct applies to all project spaces.

### Security Reporting

Security vulnerabilities are reported privately according to `SECURITY.md`.

### Roadmap Management

Roadmap changes require issue or discussion context, maintainer review, documentation updates, and milestone alignment.

## 14. Engineering Decision Process

### Architecture Decisions

Major architecture decisions require an ADR. ADRs document context, decision, alternatives, consequences, and migration impact.

### API Evolution

API changes require:

- SRS or API specification alignment.
- Documentation update.
- Tests.
- Changelog entry.
- Deprecation plan for breaking changes.

### Breaking Changes

Breaking changes require maintainer approval, semantic versioning impact, migration guide, release notes, and compatibility review.

### Experimental Features

Experimental features must be clearly labeled. They may have weaker compatibility guarantees but still require tests and documentation.

### Official Plugin Support

A plugin becomes officially supported only after:

- Maintainer review.
- Conformance tests.
- Documentation.
- CI coverage where practical.
- Compatibility policy.
- Security review for external tooling.

## 15. Long-Term Maintenance

### 1-Year Policy

Focus on core correctness, contributor onboarding, stable configuration, benchmark execution, reports, packaging, and early plugin contracts.

### 3-Year Policy

Maintain stable APIs, grow backend coverage, improve documentation, support embedded and simulator workflows, and establish plugin conformance practices.

### 5-Year Policy

Support multiple hardware ecosystems, mature dashboard workflows, benchmark campaigns, stronger supply-chain security, and broader downstream packaging.

### 10-Year Policy

Maintain AIHW-Bench as durable AI hardware infrastructure with stable data formats, migration paths, archival documentation, supported plugin ecosystems, and community governance.

### Dependency Updates

Dependencies are updated regularly with CI verification, changelog notes when user-facing, and compatibility checks.

### Python Version Support

Python support follows modern Python lifecycle expectations. Dropping a Python version requires a major or clearly documented minor release depending on pre- or post-`1.0.0` status.

### Operating System Support

Core support includes Windows, Linux, and macOS. Platform support changes require release notes and installation documentation updates.

### Deprecation Policy

Deprecated features remain available through the documented deprecation window unless there is a security reason for faster removal.

### Migration Guides

Migration guides are required for breaking public API, CLI, configuration, plugin API, report format, or persisted schema changes.
