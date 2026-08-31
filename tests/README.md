# Test Suite

The AIHW-Bench test suite is organized by risk and scope.

Required categories:

- `unit`: isolated domain, utility, configuration, validation, and metric tests.
- `integration`: subsystem collaboration tests.
- `cli`: command-line behavior and exit-code tests.
- `regression`: tests preserving bug fixes and edge cases.
- `performance`: framework overhead and large-session validation tests.
- `fixtures`: deterministic files and data used by tests.

Hardware-dependent and optional-runtime tests must be marked so the default CI suite remains portable.

Milestone 10 requires the default suite to remain reproducible on developer laptops and CI workers:

- Use fake backends, fake hardware inspectors, and fake optional runtime modules for core tests.
- Keep performance tests deterministic and focused on framework overhead, not host hardware speed.
- Generate `coverage.xml` and `htmlcov` on every full test run.
- Maintain total coverage above 95%; coverage regressions fail CI.
