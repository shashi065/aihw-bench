# Contribution Standards

## Contribution Principles

All contributions follow the project constitution. Correctness, reproducibility, documentation, static typing, and clean architecture are required.

## Required Pull Request Evidence

Every pull request should explain:

- What changed.
- Why the change is needed.
- Which architecture boundary is affected.
- How the change was tested.
- Whether public APIs, CLI behavior, configuration, plugins, reports, or persisted data changed.

## Required Updates

Feature changes require:

- Implementation documentation.
- API or CLI examples when public behavior changes.
- Tests covering normal and failure paths.
- Changelog entry when user-facing behavior changes.
- Migration notes for compatibility impact.

## Architecture Review

Maintainers review:

- Dependency direction.
- Module responsibility.
- Public API stability.
- Plugin compatibility.
- Data model evolution.
- Security impact.
- Benchmark overhead impact.

## Release Readiness

A feature is release-ready when CI passes, documentation builds, examples remain valid, and package metadata remains correct.
