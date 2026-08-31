# Contributing

Thank you for considering a contribution to AI Hardware Benchmark Suite.

The project is developed as a production-quality open-source package. Contributions should preserve clean architecture boundaries, strict typing, deterministic tests, and documented public behavior.

All contributions must follow the [AIHW-Bench Project Constitution](CONSTITUTION.md). When the constitution and convenience conflict, the constitution wins.

Contributors must also follow the [Engineering Handbook](docs/engineering/engineering-handbook.md), which defines repository, coding, testing, documentation, review, release, security, and long-term maintenance standards.

## Development Setup

```bash
python -m pip install --upgrade pip
python -m pip install poetry
poetry install --with dev,docs
poetry run pre-commit install
```

## Quality Gates

Before opening a pull request, run:

```bash
poetry run ruff check .
poetry run black --check .
poetry run mypy src
poetry run pytest --cov=aihw_bench --cov-report=term-missing
poetry run mkdocs build --strict
```

## Design Expectations

- Keep domain entities independent of framework and infrastructure code.
- Add or change public APIs only with tests and documentation.
- Prefer extension points over hard-coded backend behavior.
- Use small modules, explicit names, and Pydantic models at boundaries.
- Avoid optional heavy runtime dependencies in core paths.

## Pull Request Checklist

- Tests cover changed behavior.
- Documentation reflects user-facing behavior.
- CLI changes include CLI tests.
- New extension points include plugin documentation.
- Performance-sensitive changes include benchmark evidence or rationale.
- The change follows the project constitution.
