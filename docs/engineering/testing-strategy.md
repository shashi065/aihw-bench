# Testing Strategy

## Goals

- Keep required coverage above 95% for source code covered by the default test suite.
- Keep fast unit tests independent of heavy AI runtimes.
- Cover CLI behavior, failure modes, plugin loading, configuration precedence, storage immutability, and report generation.
- Preserve benchmark determinism through fake clocks and fake backends.

## Test Types

### Unit Tests

Unit tests cover domain models, configuration merging, metric computation, comparison policies, error classification, and individual adapter behavior.

### Integration Tests

Integration tests validate use-case flows across application and infrastructure implementations, including filesystem session storage, benchmark orchestration, plugin loading, and built-in reporters.

### CLI Tests

CLI tests use Typer's test runner to validate command output, exit codes, option precedence, and machine-readable output.

### Regression Tests

Regression tests preserve previously fixed edge cases such as malformed plugin descriptors, partial benchmark failures, corrupted session files, missing optional runtime dependencies, report failures, and cleanup recovery.

### Performance Tests

Required performance tests use deterministic fakes and scripted timing engines. They guard framework overhead and accidental algorithmic slowdowns without depending on CPU, GPU, or lab-machine performance.

### Optional Backend Tests

PyTorch, ONNX Runtime, TensorFlow Lite, GPU, simulator, and vendor SDK tests run only when dependencies and hardware are available. CI marks these as optional matrices or scheduled jobs.

## CI Quality Gates

- `ruff check .`
- `black --check .`
- `mypy src`
- `pytest --cov=aihw_bench --cov-fail-under=95`
- `mkdocs build --strict`
- `python -m build`

## Test Data

Test fixtures should be small, deterministic, and checked into `tests/fixtures` when license-compatible. Shared fake infrastructure belongs in `tests/conftest.py`. Large models and hardware-specific traces should be downloaded only in optional jobs.

## Coverage Policy

Coverage failures block CI. The default pytest run emits terminal, XML, and HTML coverage reports. Generated files and optional dependency branches may be excluded only with documented rationale.
