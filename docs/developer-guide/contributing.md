# Contributing Guide

AIHW-Bench contributions must preserve the implemented architecture and quality gates.

## Local Setup

```bash
python -m pip install --upgrade pip
python -m pip install poetry
poetry install --with dev,docs
```

## Required Checks

Run these before opening a pull request:

```bash
poetry run ruff check src tests
poetry run black --check src tests
poetry run mypy src
poetry run pytest
poetry run mkdocs build --strict
```

The test suite enforces at least 95% coverage and writes `coverage.xml` plus `htmlcov`.

## Contribution Rules

- Keep changes scoped to the milestone or issue.
- Preserve public APIs unless the change is explicitly approved.
- Add tests for new behavior and regression tests for bug fixes.
- Update user, developer, and API documentation when behavior changes.
- Use typed domain errors for expected failures.
- Keep plugin failures isolated unless strict mode is requested.

## Pull Request Checklist

- Configuration and CLI examples still match implemented options.
- New modules are reachable from the appropriate package boundary.
- Documentation builds without strict MkDocs warnings.
- Tests are deterministic and do not require specific host hardware.
