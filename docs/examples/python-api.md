# Example: Python API

The Python API is useful for tests, notebooks, and applications that need direct access to session objects.

```python
from aihw_bench.application import BenchmarkRequest, BenchmarkService, ScriptedTimingEngine
from aihw_bench.domain.models import Configuration, ExecutionConfig
from aihw_bench.infrastructure.backends import ReferenceBenchmarkBackend

configuration = Configuration(
    execution=ExecutionConfig(warmup_iterations=0, iterations=2),
)

service = BenchmarkService(
    ReferenceBenchmarkBackend(),
    timing_engine=ScriptedTimingEngine([0.01, 0.02]),
)

outcome = service.run(
    BenchmarkRequest(
        session_id="api-demo",
        configuration=configuration,
    )
)

print(outcome.result.summary)
```

Use injected timing engines, fake backends, and temporary session stores for deterministic tests.
