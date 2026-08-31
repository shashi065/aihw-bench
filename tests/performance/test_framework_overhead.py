from __future__ import annotations

import time

from tests.conftest import FakeBackend, FakeHardwareInspector

from aihw_bench.application import BenchmarkRequest, BenchmarkService, ScriptedTimingEngine
from aihw_bench.domain.models import Configuration, ExecutionConfig, SessionStatus


def test_reference_benchmark_framework_overhead_stays_small() -> None:
    """Guard deterministic benchmark orchestration from accidental slowdowns."""
    iterations = 100
    service = BenchmarkService(
        FakeBackend(),
        hardware_inspector=FakeHardwareInspector(),
        timing_engine=ScriptedTimingEngine([0.001] * iterations),
    )
    request = BenchmarkRequest(
        session_id="performance-budget",
        configuration=Configuration(
            execution=ExecutionConfig(warmup_iterations=0, iterations=iterations),
        ),
    )

    started = time.perf_counter()
    outcome = service.run(request)
    elapsed = time.perf_counter() - started

    assert outcome.session.status is SessionStatus.COMPLETED
    assert outcome.statistics["count"] == float(iterations)
    assert elapsed < 1.0
