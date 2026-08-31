# AI Hardware Benchmark Suite

AI Hardware Benchmark Suite (`aihw-bench`) is an open-source Python framework for reproducible benchmarking and profiling of AI workloads across CPUs, supported GPUs, embedded targets, simulator-backed environments, and extensible hardware backends.

## Current Release

**v2.0.0** is feature complete. It provides the benchmark engine, reproducible official-suite contracts, hardware capability reporting, static reports and dashboards, local workspace/history foundations, and a deterministic **local benchmark analysis assistant**. The assistant is metric-grounded and is not an LLM-backed service.

Hardware detection, capability reporting, executable backends, and accelerated execution are distinct concepts. See the [hardware support guide](docs/developer-guide/hardware-support.md) before selecting a device target.

## CLI

```bash
aihw-bench benchmark
aihw-bench profile
aihw-bench compare
aihw-bench report
aihw-bench dashboard
aihw-bench suite list
aihw-bench assistant SESSION_ID
aihw-bench version
```

## Documentation

Start with [docs/index.md](docs/index.md). Key current guides:

- [Hardware support](docs/developer-guide/hardware-support.md)
- [Official benchmark suite](docs/benchmarks/official-suite.md)
- [Dashboard](docs/user-guide/dashboard.md)
- [Local benchmark analysis assistant](docs/user-guide/assistant.md)
- [Enterprise foundations](docs/enterprise.md)
- [Security policy](SECURITY.md)

## Development

This repository targets Python 3.12+ and uses Poetry-compatible PEP 621 metadata.

```bash
python -m pip install --upgrade pip
python -m pip install poetry
poetry install --with dev,docs
poetry run pytest
poetry run ruff check .
poetry run mypy src
```

## License

Apache License 2.0. See [LICENSE](LICENSE).
