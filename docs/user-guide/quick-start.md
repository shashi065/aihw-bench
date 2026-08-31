# Quick Start

The benchmark engine is available through both the Python API and the `aihw-bench` CLI. The built-in reference backend is deterministic, which makes it the best first run.

## Python API

```python
from aihw_bench.application import BenchmarkRequest, BenchmarkService, ScriptedTimingEngine
from aihw_bench.domain.models import Configuration, ExecutionConfig
from aihw_bench.infrastructure.backends import ReferenceBenchmarkBackend

service = BenchmarkService(
    ReferenceBenchmarkBackend(),
    timing_engine=ScriptedTimingEngine([0.01, 0.02]),
)

outcome = service.run(
    BenchmarkRequest(
        session_id="demo-session",
        configuration=Configuration(
            execution=ExecutionConfig(warmup_iterations=0, iterations=2),
        ),
    )
)

print(outcome.result.summary)
```

## CLI

```bash
aihw-bench doctor
aihw-bench benchmark --config examples/configs/reference-benchmark.yaml
aihw-bench report demo-session --format markdown --format html
```

Use `aihw-bench config --output yaml` before a run when you need to verify merged configuration values.
