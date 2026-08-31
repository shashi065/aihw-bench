# AIHW-Bench Project Constitution

Version: 1.0

This constitution defines the permanent engineering rules for AI Hardware Benchmark Suite. Every future implementation must follow these rules. These rules override convenience.

## Vision

AIHW-Bench will become the world's leading open-source benchmarking framework for artificial intelligence hardware.

The project should support researchers, hardware engineers, FPGA engineers, ASIC designers, ML engineers, embedded engineers, compiler developers, and AI accelerator developers.

The framework should benchmark everything from laptops to future custom silicon.

## Mission

Provide a modern benchmarking framework that makes AI hardware evaluation reproducible, extensible, accurate, and developer-friendly.

## Project Values

1. Correctness before speed.
2. Performance before unnecessary abstraction.
3. Simple APIs.
4. Professional documentation.
5. Stable interfaces.
6. Readable code.
7. Strong testing.
8. Reproducible benchmarks.
9. Open-source first.
10. Backward compatibility whenever practical.

## Non-Negotiable Rules

- Never merge broken code.
- Never commit failing tests.
- Never remove documentation.
- Never introduce duplicated logic.
- Never create dead code.
- Never ignore static typing.
- Never break public APIs without versioning.
- Never use placeholder implementations.
- Never leave unfinished modules.

## Architecture Rules

- Every module must have a single responsibility.
- Every subsystem must expose clean interfaces.
- Dependencies must always point inward.
- Circular imports are not allowed.
- Hidden global state is not allowed.
- Business logic must never depend on CLI code.
- Visualization must never depend directly on benchmark execution.
- Backends must remain independent.

## Coding Standards

- Python 3.12+.
- Strict typing.
- Meaningful variable names.
- Meaningful module names.
- Descriptive class names.
- Descriptive exceptions.
- PEP 8.
- PEP 257.
- Google-style docstrings.
- Small functions.
- Pure functions whenever practical.
- No hardcoded values in behavior that should be configurable.

## API Design

Public APIs must remain stable.

Every public API must include:

- Type hints.
- Examples.
- Documentation.
- Error descriptions.
- Version history when behavior changes.
- Deprecation notices when necessary.

## Package Design

The package must be installable using `pip` and `uv`.

The package must expose:

- Python API.
- Command line interface.
- Plugin interface.

## Module Organization

- Every module should remain independent.
- No file should become excessively large.
- Large modules must be split logically.

## Performance

- Benchmark overhead should remain minimal.
- Avoid unnecessary allocations.
- Prefer vectorized operations where they improve clarity and performance.
- Cache repeated calculations when it does not compromise correctness.
- Profile expensive operations before optimizing them.

## Security

- Never execute arbitrary code.
- Validate all inputs.
- Handle malformed files gracefully.
- Avoid insecure deserialization.
- Protect against path traversal.
- Never expose secrets.

## Error Handling

Every expected error should include:

- Cause.
- Suggested solution.
- Relevant documentation.

CLI errors must remain user friendly.

## Documentation

- Every feature requires documentation.
- Every command requires examples.
- Every public class requires documentation.
- Architecture diagrams should remain updated.

## Testing

Every new feature must include:

- Unit tests.
- Integration tests.
- Regression tests when applicable.
- CLI tests.
- Performance validation when relevant.

## Release Policy

Every release requires:

- Passing CI.
- Updated changelog.
- Release notes.
- Documentation updates.
- Version bump.
- Tagged GitHub release.
- PyPI-ready artifacts.

## Open Source Policy

The following must remain updated:

- Issue templates.
- Pull request template.
- Contribution guide.
- Security policy.
- Code of conduct.
- Roadmap.
- Community documentation.

## Maintainability

When better architecture becomes available, maintainers should refactor responsibly, maintain backward compatibility where practical, and document migration steps.

## Long-Term Goal

AIHW-Bench should eventually become a standard benchmarking framework used across AI hardware research, RTL simulation, FPGA development, embedded AI systems, and accelerator design.

Every engineering decision should move the repository toward that vision.
