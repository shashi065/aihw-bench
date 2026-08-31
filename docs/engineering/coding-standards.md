# Coding Standards

## Language and Typing

- Python 3.12+.
- Strict typing.
- Public APIs use explicit type hints.
- Avoid `Any` unless it models genuinely dynamic plugin metadata and is validated at boundaries.

## Style

- PEP 8.
- PEP 257.
- Google-style docstrings.
- Ruff, Black, and mypy are mandatory quality gates.

## Design

- Single responsibility per module.
- Small functions.
- Descriptive exceptions.
- Pure functions where practical.
- Dependency injection for replaceable collaborators.
- No hidden global state.
- No circular imports.

## API Documentation

Every public API requires:

- Purpose.
- Inputs.
- Outputs.
- Exceptions.
- Example usage.
- Version history when behavior changes.
- Deprecation notes when applicable.

## Error Messages

Expected errors include:

- Cause.
- Suggested solution.
- Documentation reference.

CLI messages are concise. Logs may include deeper diagnostics when safe.

## Review Rules

Changes are not ready unless they include tests, documentation, typing, and release notes when user-facing behavior changes.
