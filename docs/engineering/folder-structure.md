# Folder Structure Specification

## Target Layout

```text
aihw-bench/
  .github/
    workflows/
  docs/
    engineering/
    user-guide/
    developer-guide/
  examples/
    configs/
    plugins/
    reports/
  src/
    aihw_bench/
      __init__.py
      domain/
      application/
      infrastructure/
      presentation/
      utils/
  tests/
    unit/
    integration/
    cli/
    regression/
  pyproject.toml
  mkdocs.yml
```

## Package Boundaries

- `domain`: pure business rules, models, value objects, and ports.
- `application`: use-case orchestration and dependency-injected services.
- `infrastructure`: concrete adapters for filesystems, runtimes, reporting, profiling, plugins, and system inspection.
- `presentation`: CLI and future dashboard entry points.
- `utils`: narrow technical helpers that do not depend on application or infrastructure.

## Import Rules

- `domain` imports only Python standard library, Pydantic, and local domain modules.
- `application` may import `domain` and local utilities.
- `infrastructure` may import `domain`, `application` command/result models, and third-party implementation dependencies.
- `presentation` may import `application`, `infrastructure` composition roots, and display libraries.
- Tests may import any package layer but should prefer public APIs for integration tests.

## Documentation Ownership

- Engineering specs live under `docs/engineering`.
- End-user documentation lives under `docs/user-guide`.
- Contributor and maintainer documentation lives under `docs/developer-guide`.
- Public API reference will be generated from typed source code after implementation begins.
