"""Benchmark execution engine and supporting helpers."""

from __future__ import annotations

import logging
import platform
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, ClassVar, Generic, Protocol, TypeVar, runtime_checkable

from aihw_bench.application.metrics import CoreMetricsEngine, StatisticalAggregator
from aihw_bench.application.reports import ReportRequest, ReportService
from aihw_bench.domain.errors import ModelError, RuntimeExecutionError, ValidationError
from aihw_bench.domain.model_support import ModelLoaderCatalog
from aihw_bench.domain.models import (
    BenchmarkResult,
    BenchmarkSession,
    Configuration,
    Diagnostic,
    DiagnosticSeverity,
    ExecutionPhase,
    ExecutionResult,
    ExecutionStatus,
    HardwareProfile,
    ModelMetadata,
    SessionStatus,
)
from aihw_bench.domain.ports import BackendRegistry, BenchmarkBackend, HardwareInspector
from aihw_bench.infrastructure.storage import FilesystemSessionStore

T = TypeVar("T")


class BenchmarkLifecycleState(StrEnum):
    """Lifecycle states for benchmark orchestration."""

    CREATED = "created"
    PREPARED = "prepared"
    WARMING = "warming"
    MEASURING = "measuring"
    AGGREGATING = "aggregating"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class BenchmarkStep:
    """One scheduled benchmark step."""

    phase: ExecutionPhase
    iteration: int
    attempt: int = 0


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Ordered execution steps for a benchmark session."""

    steps: tuple[BenchmarkStep, ...]
    warmup_iterations: int
    measured_iterations: int

    @property
    def measured_steps(self) -> tuple[BenchmarkStep, ...]:
        """Return the measured steps only."""
        return tuple(step for step in self.steps if step.phase is ExecutionPhase.MEASUREMENT)


@dataclass(frozen=True, slots=True)
class TimingSample(Generic[T]):
    """A timed operation result with timestamps and a payload."""

    started_at: datetime
    ended_at: datetime
    duration_seconds: float
    value: T


@runtime_checkable
class TimingEngine(Protocol):
    """Measure a callable and return timestamps and duration."""

    def measure(self, operation: Callable[[], T]) -> TimingSample[T]:
        """Execute one operation and measure its duration."""


class MonotonicTimingEngine:
    """High-resolution timing engine backed by the system monotonic clock."""

    def measure(self, operation: Callable[[], T]) -> TimingSample[T]:
        started_at = datetime.now(UTC)
        start = time.perf_counter()
        value = operation()
        duration_seconds = time.perf_counter() - start
        ended_at = started_at + timedelta(seconds=duration_seconds)
        return TimingSample(
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
            value=value,
        )


class ScriptedTimingEngine:
    """Deterministic timing engine for tests and smoke validation."""

    def __init__(self, durations: Sequence[float], *, origin: datetime | None = None) -> None:
        self._durations = list(durations)
        self._origin = origin or datetime(2026, 1, 1, tzinfo=UTC)
        self._current = self._origin
        self._index = 0

    def measure(self, operation: Callable[[], T]) -> TimingSample[T]:
        if self._index >= len(self._durations):
            raise RuntimeExecutionError(
                "Scripted timing data was exhausted.",
                cause="No scripted duration remained for the requested operation.",
                suggestion="Provide enough scripted durations for the benchmark plan.",
                documentation="docs/engineering/benchmark-engine.md",
            )

        duration_seconds = self._durations[self._index]
        self._index += 1
        started_at = self._current
        value = operation()
        ended_at = started_at + timedelta(seconds=duration_seconds)
        self._current = ended_at
        return TimingSample(
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
            value=value,
        )


class ExecutionScheduler:
    """Build a deterministic execution plan for warmup and measured iterations."""

    def plan(self, *, warmup_iterations: int, iterations: int) -> ExecutionPlan:
        if warmup_iterations < 0:
            raise ValidationError(
                "Warmup iterations must be non-negative.",
                cause=f"{warmup_iterations} is less than zero.",
                suggestion="Use zero or a positive warmup count.",
                documentation="docs/engineering/benchmark-engine.md",
            )
        if iterations < 1:
            raise ValidationError(
                "Measured iterations must be positive.",
                cause=f"{iterations} is less than one.",
                suggestion="Use at least one measured iteration.",
                documentation="docs/engineering/benchmark-engine.md",
            )

        steps = [
            *(
                BenchmarkStep(phase=ExecutionPhase.WARMUP, iteration=index)
                for index in range(warmup_iterations)
            ),
            *(
                BenchmarkStep(phase=ExecutionPhase.MEASUREMENT, iteration=index)
                for index in range(iterations)
            ),
        ]
        return ExecutionPlan(
            steps=tuple(steps),
            warmup_iterations=warmup_iterations,
            measured_iterations=iterations,
        )


class StatisticsEngine:
    """Compatibility facade for the canonical :class:`StatisticalAggregator`.

    Historical callers receive duration-specific field names while all numeric
    calculations are delegated to the single metrics implementation.
    """

    def __init__(self, aggregator: StatisticalAggregator | None = None) -> None:
        self._aggregator = aggregator or StatisticalAggregator()

    def summarize(self, durations: Sequence[float]) -> dict[str, float]:
        """Return duration statistics using the stable benchmark-engine schema."""
        if not durations:
            raise ValidationError(
                "At least one measured duration is required.",
                cause="No durations were provided.",
                suggestion="Collect at least one measured benchmark result.",
                documentation="docs/engineering/benchmark-engine.md",
            )
        summary = self._aggregator.summarize(durations)
        total_duration = summary["total"]
        measured_count = summary["count"]
        return {
            "count": measured_count,
            "min_seconds": summary["min"],
            "max_seconds": summary["max"],
            "mean_seconds": summary["mean"],
            "median_seconds": summary["median"],
            "stdev_seconds": summary["stdev"],
            "p95_seconds": summary["p95"],
            "p99_seconds": summary["p99"],
            "total_seconds": total_duration,
            "throughput_iterations_per_second": (
                measured_count / total_duration if total_duration > 0 else 0.0
            ),
        }

    @staticmethod
    def _percentile(values: Sequence[float], percentile: float) -> float:
        """Compatibility entry point delegated to the canonical aggregator."""
        return StatisticalAggregator._percentile(values, percentile)


@dataclass(frozen=True, slots=True)
class BenchmarkRequest:
    """Validated benchmark request accepted by the benchmark service."""

    session_id: str
    configuration: Configuration
    workload: ModelMetadata | None = None
    hardware: HardwareProfile = field(default_factory=HardwareProfile)


@dataclass(frozen=True, slots=True)
class BenchmarkOutcome:
    """Result returned by the benchmark service."""

    session: BenchmarkSession
    result: BenchmarkResult
    plan: ExecutionPlan
    state: BenchmarkLifecycleState
    statistics: dict[str, float]


class LifecycleTracker:
    """Validate benchmark lifecycle transitions."""

    _allowed_transitions: ClassVar[dict[BenchmarkLifecycleState, set[BenchmarkLifecycleState]]] = {
        BenchmarkLifecycleState.CREATED: {
            BenchmarkLifecycleState.PREPARED,
            BenchmarkLifecycleState.FAILED,
        },
        BenchmarkLifecycleState.PREPARED: {
            BenchmarkLifecycleState.WARMING,
            BenchmarkLifecycleState.MEASURING,
            BenchmarkLifecycleState.FAILED,
        },
        BenchmarkLifecycleState.WARMING: {
            BenchmarkLifecycleState.MEASURING,
            BenchmarkLifecycleState.FAILED,
        },
        BenchmarkLifecycleState.MEASURING: {
            BenchmarkLifecycleState.AGGREGATING,
            BenchmarkLifecycleState.FAILED,
        },
        BenchmarkLifecycleState.AGGREGATING: {
            BenchmarkLifecycleState.FINALIZING,
            BenchmarkLifecycleState.FAILED,
        },
        BenchmarkLifecycleState.FINALIZING: {
            BenchmarkLifecycleState.COMPLETED,
            BenchmarkLifecycleState.FAILED,
        },
        BenchmarkLifecycleState.COMPLETED: set(),
        BenchmarkLifecycleState.FAILED: set(),
    }

    def __init__(self) -> None:
        self._state = BenchmarkLifecycleState.CREATED

    @property
    def state(self) -> BenchmarkLifecycleState:
        """Return the current lifecycle state."""
        return self._state

    def transition(self, new_state: BenchmarkLifecycleState) -> None:
        """Move to a new lifecycle state if the transition is valid."""
        allowed_states = self._allowed_transitions[self._state]
        if new_state not in allowed_states:
            raise ValidationError(
                "Invalid benchmark lifecycle transition.",
                cause=f"{self._state.value} cannot transition to {new_state.value}.",
                suggestion="Advance the benchmark through the expected lifecycle phases.",
                documentation="docs/engineering/benchmark-engine.md",
            )
        self._state = new_state


class BenchmarkService:
    """Coordinate benchmark execution over a configured backend."""

    def __init__(
        self,
        backend: BenchmarkBackend | None = None,
        *,
        backend_registry: BackendRegistry | None = None,
        hardware_inspector: HardwareInspector | None = None,
        model_catalog: ModelLoaderCatalog | None = None,
        timing_engine: TimingEngine | None = None,
        scheduler: ExecutionScheduler | None = None,
        statistics_engine: StatisticsEngine | None = None,
        metrics_engine: CoreMetricsEngine | None = None,
        report_service: ReportService | None = None,
        session_store: FilesystemSessionStore | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.backend = backend
        self.backend_registry = backend_registry
        self.hardware_inspector = hardware_inspector
        self.model_catalog = model_catalog
        self.timing_engine = timing_engine or MonotonicTimingEngine()
        self.scheduler = scheduler or ExecutionScheduler()
        self.statistics_engine = statistics_engine or StatisticsEngine()
        self.metrics_engine = metrics_engine or CoreMetricsEngine()
        self.report_service = report_service
        self.session_store = session_store
        self.logger = logger or logging.getLogger("aihw_bench.benchmark")

    def run(self, request: BenchmarkRequest) -> BenchmarkOutcome:
        """Run one benchmark session and return the final immutable session record."""
        plan = self.scheduler.plan(
            warmup_iterations=request.configuration.execution.warmup_iterations,
            iterations=request.configuration.execution.iterations,
        )
        tracker = LifecycleTracker()
        tracker.transition(BenchmarkLifecycleState.PREPARED)
        self.logger.info(
            "Starting benchmark session %s with %s warmup and %s measured iterations.",
            request.session_id,
            plan.warmup_iterations,
            plan.measured_iterations,
        )

        hardware = self._resolve_hardware(request)
        backend = self._resolve_backend(request, hardware)

        base_session = BenchmarkSession(
            session_id=request.session_id,
            status=SessionStatus.RUNNING,
            configuration=request.configuration,
            hardware=hardware,
            workload=request.workload,
            system=self._system_metadata(),
            backend={"name": backend.name, "version": backend.version},
        )

        diagnostics: list[Diagnostic] = []
        runs: list[ExecutionResult] = []
        durations: list[float] = []
        backend_metadata: dict[str, Any] = {}
        failure_message: str | None = None
        cleanup_error: Exception | None = None
        benchmark_outcome: BenchmarkOutcome | None = None

        try:
            session_workload = self._resolve_workload(request)
            if session_workload is not None:
                base_session = base_session.model_copy(update={"workload": session_workload})
            backend_metadata = self._prepare_backend(request, backend, hardware)
            for step in plan.steps:
                current_step = step
                while True:
                    desired_state = (
                        BenchmarkLifecycleState.WARMING
                        if current_step.phase is ExecutionPhase.WARMUP
                        else BenchmarkLifecycleState.MEASURING
                    )
                    if tracker.state is not desired_state:
                        tracker.transition(desired_state)
                    execution_result, succeeded = self._execute_step(
                        request,
                        current_step,
                        backend_metadata,
                        backend,
                        hardware,
                    )
                    runs.append(execution_result)
                    if current_step.phase is ExecutionPhase.MEASUREMENT and succeeded:
                        durations.append(execution_result.duration_seconds)
                        failure_message = None
                        break

                    if not succeeded:
                        failure_message = execution_result.error or "Benchmark step failed."
                        if (
                            current_step.phase is ExecutionPhase.MEASUREMENT
                            and current_step.attempt
                            < request.configuration.execution.retry_attempts
                        ):
                            self.logger.warning(
                                "Retrying measurement %s attempt %s after failure.",
                                current_step.iteration,
                                current_step.attempt + 1,
                            )
                            current_step = BenchmarkStep(
                                phase=current_step.phase,
                                iteration=current_step.iteration,
                                attempt=current_step.attempt + 1,
                            )
                            continue
                        break

                    break

                if failure_message is not None:
                    break

            if failure_message is None:
                tracker.transition(BenchmarkLifecycleState.AGGREGATING)
                statistics = self.statistics_engine.summarize(durations)
                final_status = SessionStatus.COMPLETED
                final_state = BenchmarkLifecycleState.COMPLETED
            elif durations and tracker.state is BenchmarkLifecycleState.MEASURING:
                tracker.transition(BenchmarkLifecycleState.AGGREGATING)
                statistics = self.statistics_engine.summarize(durations)
                final_status = SessionStatus.PARTIAL
                final_state = BenchmarkLifecycleState.FAILED
            else:
                statistics = {}
                final_status = SessionStatus.FAILED
                final_state = BenchmarkLifecycleState.FAILED

            if failure_message is not None:
                diagnostics.append(
                    Diagnostic(
                        code="benchmark.execution_failed",
                        message="Benchmark execution failed.",
                        severity=DiagnosticSeverity.ERROR,
                        cause=failure_message,
                        suggestion=(
                            "Inspect the backend, timing engine, and benchmark configuration."
                        ),
                        documentation="docs/engineering/benchmark-engine.md",
                    )
                )

            benchmark_result = self._build_result(
                request=request,
                runs=runs,
                hardware=hardware,
                workload=base_session.workload,
                statistics=statistics,
                failure_message=failure_message,
            )
            statistics = benchmark_result.statistics
            if final_state is BenchmarkLifecycleState.COMPLETED:
                tracker.transition(BenchmarkLifecycleState.FINALIZING)
                tracker.transition(BenchmarkLifecycleState.COMPLETED)
            elif tracker.state is not BenchmarkLifecycleState.FAILED:
                tracker.transition(BenchmarkLifecycleState.FAILED)
            final_session = base_session.model_copy(
                update={
                    "runs": runs,
                    "results": [benchmark_result],
                    "metrics": benchmark_result.primary_metrics
                    + benchmark_result.secondary_metrics,
                    "diagnostics": diagnostics,
                    "backend": {**base_session.backend, **backend_metadata},
                }
            ).finalize(final_status)
            benchmark_outcome = BenchmarkOutcome(
                session=final_session,
                result=benchmark_result,
                plan=plan,
                state=tracker.state,
                statistics=statistics,
            )
        except Exception as exc:
            diagnostics.append(
                Diagnostic(
                    code="benchmark.execution_failed",
                    message="Benchmark execution failed.",
                    severity=DiagnosticSeverity.ERROR,
                    cause=str(exc),
                    suggestion="Inspect the backend, timing engine, and benchmark configuration.",
                    documentation="docs/engineering/benchmark-engine.md",
                )
            )
            if tracker.state not in {
                BenchmarkLifecycleState.FAILED,
                BenchmarkLifecycleState.COMPLETED,
            }:
                tracker.transition(BenchmarkLifecycleState.FAILED)
            final_session = base_session.model_copy(
                update={
                    "runs": runs,
                    "diagnostics": diagnostics,
                    "backend": {**base_session.backend, **backend_metadata},
                }
            ).finalize(SessionStatus.FAILED if not durations else SessionStatus.PARTIAL)
            benchmark_result = self._build_result(
                request=request,
                runs=runs,
                hardware=hardware,
                workload=base_session.workload,
                statistics={"count": 0.0},
                failure_message=str(exc),
            )
            benchmark_outcome = BenchmarkOutcome(
                session=final_session,
                result=benchmark_result,
                plan=plan,
                state=tracker.state,
                statistics={"count": 0.0},
            )
        finally:
            try:
                backend.cleanup()
            except Exception as cleanup_exc:
                cleanup_error = cleanup_exc
                self.logger.exception("Benchmark cleanup failed: %s", cleanup_exc)

        if benchmark_outcome is None:
            raise RuntimeExecutionError(
                "Benchmark execution did not produce an outcome.",
                cause="The benchmark service completed without building a result.",
                suggestion="Inspect the benchmark service control flow.",
                documentation="docs/engineering/benchmark-engine.md",
            )

        if cleanup_error is not None:
            cleanup_diagnostic = Diagnostic(
                code="benchmark.cleanup_failed",
                message="Benchmark cleanup failed.",
                severity=DiagnosticSeverity.ERROR,
                cause=str(cleanup_error),
                suggestion="Inspect backend cleanup and resource release logic.",
                documentation="docs/engineering/benchmark-engine.md",
            )
            updated_session = benchmark_outcome.session.model_copy(
                update={
                    "diagnostics": [*benchmark_outcome.session.diagnostics, cleanup_diagnostic],
                    "status": (
                        SessionStatus.PARTIAL
                        if benchmark_outcome.session.status is SessionStatus.COMPLETED
                        else benchmark_outcome.session.status
                    ),
                }
            )
            updated_result = benchmark_outcome.result.model_copy(
                update={
                    "status": ExecutionStatus.FAILED,
                    "error": str(cleanup_error),
                }
            )
            benchmark_outcome = BenchmarkOutcome(
                session=updated_session,
                result=updated_result,
                plan=benchmark_outcome.plan,
                state=BenchmarkLifecycleState.FAILED,
                statistics=benchmark_outcome.statistics,
            )

        if self.session_store is not None:
            self.session_store.create(benchmark_outcome.session)

        if self.report_service is not None:
            try:
                self.report_service.generate(ReportRequest(session=benchmark_outcome.session))
            except Exception as exc:
                self.logger.exception("Report generation failed: %s", exc)

        return benchmark_outcome

    def _resolve_backend(
        self, request: BenchmarkRequest, hardware: HardwareProfile
    ) -> BenchmarkBackend:
        """Resolve the backend either from the injected backend or the registry."""
        if self.backend is not None:
            if self.backend_registry is not None:
                self.backend_registry.validate(
                    self.backend, request.configuration, hardware, request.workload
                )
            return self.backend
        if self.backend_registry is None:
            raise RuntimeExecutionError(
                "No backend was configured.",
                cause="Neither a backend instance nor a backend registry was provided.",
                suggestion="Pass a backend or a backend registry to the benchmark service.",
                documentation="docs/developer-guide/backend-support.md",
            )
        return self.backend_registry.select(request.configuration, hardware, request.workload)

    def _resolve_hardware(self, request: BenchmarkRequest) -> HardwareProfile:
        """Return the requested hardware profile or inspect the current host."""
        if request.hardware != HardwareProfile():
            return request.hardware
        if self.hardware_inspector is None:
            from aihw_bench.infrastructure.hardware import SystemHardwareInspector

            return SystemHardwareInspector().inspect()
        return self.hardware_inspector.inspect()

    def _resolve_workload(self, request: BenchmarkRequest) -> ModelMetadata | None:
        """Resolve the workload metadata from the request or configured loader."""
        if request.workload is not None:
            return request.workload

        workload = request.configuration.workload
        if workload.source is not None:
            if self.model_catalog is None:
                raise ModelError(
                    "Model loading was requested but no model catalog was configured.",
                    cause="workload.source is set in the configuration.",
                    suggestion="Provide a ModelLoaderCatalog when using workload.source.",
                    documentation="docs/developer-guide/model-support.md",
                )
            return self.model_catalog.load_workload(workload).metadata

        if workload.name is None and not workload.input_shapes and not workload.metadata:
            return None

        model_id = workload.name or "configured-workload"
        source = workload.source
        return ModelMetadata(
            model_id=model_id,
            name=workload.name or model_id,
            format=workload.metadata.get("format", "configured"),
            framework=workload.metadata.get("framework"),
            source=source,
            input_shapes=dict(workload.input_shapes),
            metadata=dict(workload.metadata),
        )

    def _prepare_backend(
        self,
        request: BenchmarkRequest,
        backend: BenchmarkBackend,
        hardware: HardwareProfile,
    ) -> dict[str, Any]:
        try:
            metadata = backend.prepare(
                request.configuration,
                hardware,
                request.workload,
            )
        except Exception as exc:
            raise RuntimeExecutionError(
                "Backend preparation failed.",
                cause=str(exc),
                suggestion="Inspect backend initialization and configuration values.",
                documentation="docs/engineering/benchmark-engine.md",
            ) from exc

        return dict(metadata)

    def _execute_step(
        self,
        request: BenchmarkRequest,
        step: BenchmarkStep,
        backend_metadata: Mapping[str, Any],
        backend: BenchmarkBackend,
        hardware: HardwareProfile,
    ) -> tuple[ExecutionResult, bool]:
        timeout_seconds = request.configuration.execution.timeout_seconds

        try:
            timed = self.timing_engine.measure(
                lambda: backend.execute(
                    step.phase,
                    step.iteration,
                    request.configuration,
                    hardware,
                    request.workload,
                )
            )
        except Exception as exc:
            return (
                self._failed_execution_result(
                    request=request,
                    step=step,
                    error_message=str(exc),
                    backend_metadata=backend_metadata,
                ),
                False,
            )

        observations = dict(timed.value)
        observations.setdefault("phase", step.phase.value)
        observations.setdefault("iteration", step.iteration)
        observations.setdefault("attempt", step.attempt)

        if timeout_seconds is not None and timed.duration_seconds > timeout_seconds:
            return (
                self._failed_execution_result(
                    request=request,
                    step=step,
                    error_message=(f"Execution exceeded timeout of {timeout_seconds} seconds."),
                    backend_metadata=backend_metadata,
                    started_at=timed.started_at,
                    ended_at=timed.ended_at,
                    duration_seconds=timed.duration_seconds,
                    observations=observations,
                ),
                False,
            )

        execution_result = ExecutionResult(
            execution_id=f"{request.session_id}-{step.phase.value}-{step.iteration}-attempt{step.attempt}",
            phase=step.phase,
            iteration=step.iteration,
            started_at=timed.started_at,
            ended_at=timed.ended_at,
            duration_seconds=timed.duration_seconds,
            status=ExecutionStatus.SUCCESS,
            observations=observations,
            backend_metadata={**backend_metadata, "attempt": step.attempt},
        )
        return execution_result, True

    def _failed_execution_result(
        self,
        *,
        request: BenchmarkRequest,
        step: BenchmarkStep,
        error_message: str,
        backend_metadata: Mapping[str, Any],
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        duration_seconds: float = 0.0,
        observations: Mapping[str, Any] | None = None,
    ) -> ExecutionResult:
        started = started_at or datetime.now(UTC)
        ended = ended_at or started
        return ExecutionResult(
            execution_id=f"{request.session_id}-{step.phase.value}-{step.iteration}-attempt{step.attempt}",
            phase=step.phase,
            iteration=step.iteration,
            started_at=started,
            ended_at=ended,
            duration_seconds=duration_seconds,
            status=ExecutionStatus.FAILED,
            observations=dict(observations or {}),
            backend_metadata={**backend_metadata, "attempt": step.attempt},
            error=error_message,
        )

    def _build_result(
        self,
        *,
        request: BenchmarkRequest,
        runs: Sequence[ExecutionResult],
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
        statistics: Mapping[str, float],
        failure_message: str | None,
    ) -> BenchmarkResult:
        metrics_bundle = self.metrics_engine.compute(
            session_id=request.session_id,
            configuration=request.configuration,
            runs=runs,
            hardware=hardware,
            workload=workload,
            failure_message=failure_message,
            latency_statistics=statistics if statistics else None,
        )
        result_statistics = {**dict(statistics), **metrics_bundle.statistics}
        return BenchmarkResult(
            result_id=f"{request.session_id}-result",
            session_id=request.session_id,
            status=ExecutionStatus.SUCCESS if failure_message is None else ExecutionStatus.FAILED,
            primary_metrics=metrics_bundle.primary_metrics,
            secondary_metrics=metrics_bundle.secondary_metrics,
            statistics=result_statistics,
            summary=metrics_bundle.summary,
            comparison_keys={
                "backend": request.configuration.backend.name,
                "device": request.configuration.backend.device,
                "precision": request.configuration.execution.precision,
                "batch_size": str(request.configuration.execution.batch_size),
                "profile": request.configuration.profile,
            },
            error=failure_message,
        )

    @staticmethod
    def _system_metadata() -> dict[str, str]:
        return {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "implementation": platform.python_implementation(),
        }
