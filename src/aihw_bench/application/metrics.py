"""Core metric computation for benchmark results and reporting summaries."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import fmean, median, stdev
from typing import Any

from aihw_bench.domain.errors import ValidationError
from aihw_bench.domain.models import (
    Configuration,
    ExecutionPhase,
    ExecutionResult,
    ExecutionStatus,
    HardwareProfile,
    Metric,
    MetricKind,
    ModelMetadata,
)

METRIC_SOURCE = "metrics-engine"
METRICS_DOC = "docs/developer-guide/metrics.md"


@dataclass(frozen=True, slots=True)
class MetricsBundle:
    """Computed metrics and report-ready summary data."""

    primary_metrics: list[Metric]
    secondary_metrics: list[Metric]
    statistics: dict[str, float]
    summary: dict[str, Any]

    @property
    def metrics(self) -> list[Metric]:
        """Return all computed metrics in report order."""
        return [*self.primary_metrics, *self.secondary_metrics]

    def to_report_payload(self) -> dict[str, Any]:
        """Return a stable payload for downstream report builders."""
        return {
            "summary": self.summary,
            "statistics": self.statistics,
            "metrics": [metric.model_dump(mode="json") for metric in self.metrics],
        }


class StatisticalAggregator:
    """Compute deterministic statistical summaries for numeric samples."""

    def summarize(self, values: Sequence[float]) -> dict[str, float]:
        """Return count, min, max, mean, median, standard deviation, and percentiles."""
        if not values:
            raise ValidationError(
                "At least one numeric sample is required.",
                cause="No samples were provided to the statistical aggregator.",
                suggestion="Collect successful measurements before computing metrics.",
                documentation=METRICS_DOC,
            )

        samples = [float(value) for value in values]
        sorted_samples = sorted(samples)
        total = sum(samples)
        count = float(len(samples))
        return {
            "count": count,
            "min": min(samples),
            "max": max(samples),
            "mean": fmean(samples),
            "median": median(samples),
            "stdev": stdev(samples) if len(samples) > 1 else 0.0,
            "p95": self._percentile(sorted_samples, 95.0),
            "p99": self._percentile(sorted_samples, 99.0),
            "total": total,
        }

    @staticmethod
    def _percentile(values: Sequence[float], percentile: float) -> float:
        if not values:
            raise ValidationError(
                "Cannot compute a percentile without values.",
                cause="No values were provided.",
                suggestion="Provide numeric samples before computing statistics.",
                documentation=METRICS_DOC,
            )
        if len(values) == 1:
            return float(values[0])

        rank = (len(values) - 1) * (percentile / 100.0)
        lower_index = math.floor(rank)
        upper_index = math.ceil(rank)
        lower_value = values[lower_index]
        upper_value = values[upper_index]
        if lower_index == upper_index:
            return float(lower_value)
        return float(lower_value + ((upper_value - lower_value) * (rank - lower_index)))


class ResultSerializer:
    """Serialize metric outputs for storage and report integration."""

    def bundle_to_dict(self, bundle: MetricsBundle) -> dict[str, Any]:
        """Serialize a metrics bundle with deterministic keys."""
        return bundle.to_report_payload()

    def metrics_to_dicts(self, metrics: Sequence[Metric]) -> list[dict[str, Any]]:
        """Serialize metric records for JSON, Markdown, CSV, or HTML reporters."""
        return [metric.model_dump(mode="json") for metric in metrics]


class CoreMetricsEngine:
    """Compute core latency, throughput, resource, utilization, and FLOPS metrics."""

    def __init__(self, aggregator: StatisticalAggregator | None = None) -> None:
        self.aggregator = aggregator or StatisticalAggregator()

    def compute(
        self,
        *,
        session_id: str,
        configuration: Configuration,
        runs: Sequence[ExecutionResult],
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
        failure_message: str | None = None,
        latency_statistics: Mapping[str, float] | None = None,
    ) -> MetricsBundle:
        """Compute metrics from successful measured runs and backend observations."""
        measured_runs = [
            run
            for run in runs
            if run.phase is ExecutionPhase.MEASUREMENT and run.status is ExecutionStatus.SUCCESS
        ]
        statistics = (
            dict(latency_statistics)
            if latency_statistics is not None
            else self._latency_statistics([run.duration_seconds for run in measured_runs])
        )
        observation_samples = self._collect_observation_samples(measured_runs)
        primary_metrics = self._primary_metrics(statistics)
        secondary_metrics = [
            *self._latency_metrics(statistics),
            *self._throughput_metrics(statistics, configuration),
            *self._resource_metrics(observation_samples),
            *self._flops_metrics(
                statistics, measured_runs, workload, observation_samples["operations"]
            ),
        ]
        summary = self._summary(
            session_id=session_id,
            configuration=configuration,
            hardware=hardware,
            workload=workload,
            statistics=statistics,
            metrics=[*primary_metrics, *secondary_metrics],
            failure_message=failure_message,
        )
        return MetricsBundle(
            primary_metrics=primary_metrics,
            secondary_metrics=secondary_metrics,
            statistics=statistics,
            summary=summary,
        )

    def _latency_statistics(self, durations: Sequence[float]) -> dict[str, float]:
        if not durations:
            return {"count": 0.0}

        summary = self.aggregator.summarize(durations)
        total_seconds = summary["total"]
        count = summary["count"]
        return {
            "count": count,
            "min_seconds": summary["min"],
            "max_seconds": summary["max"],
            "mean_seconds": summary["mean"],
            "median_seconds": summary["median"],
            "stdev_seconds": summary["stdev"],
            "p95_seconds": summary["p95"],
            "p99_seconds": summary["p99"],
            "total_seconds": total_seconds,
            "throughput_iterations_per_second": count / total_seconds if total_seconds > 0 else 0.0,
        }

    def _primary_metrics(self, statistics: Mapping[str, float]) -> list[Metric]:
        return [
            self._metric(
                name="latency_mean_seconds",
                display_name="Mean Latency",
                value=statistics.get("mean_seconds"),
                unit="seconds",
                kind=MetricKind.DERIVED,
                higher_is_better=False,
                assumptions=["Computed from successful measured iteration durations."],
            ),
            self._metric(
                name="throughput_iterations_per_second",
                display_name="Throughput",
                value=statistics.get("throughput_iterations_per_second"),
                unit="iterations/s",
                kind=MetricKind.DERIVED,
                higher_is_better=True,
                assumptions=["Successful measured iterations divided by measured duration."],
            ),
        ]

    def _latency_metrics(self, statistics: Mapping[str, float]) -> list[Metric]:
        definitions = [
            ("latency_min_seconds", "Minimum Latency", "min_seconds"),
            ("latency_max_seconds", "Maximum Latency", "max_seconds"),
            ("latency_median_seconds", "Median Latency", "median_seconds"),
            ("latency_p95_seconds", "95th Percentile Latency", "p95_seconds"),
            ("latency_p99_seconds", "99th Percentile Latency", "p99_seconds"),
            ("latency_stdev_seconds", "Latency Standard Deviation", "stdev_seconds"),
            ("benchmark_duration_total_seconds", "Measured Duration", "total_seconds"),
        ]
        return [
            self._metric(
                name=name,
                display_name=display_name,
                value=statistics.get(key),
                unit="seconds",
                kind=MetricKind.DERIVED,
                higher_is_better=False,
            )
            for name, display_name, key in definitions
        ]

    def _throughput_metrics(
        self,
        statistics: Mapping[str, float],
        configuration: Configuration,
    ) -> list[Metric]:
        iterations_per_second = statistics.get("throughput_iterations_per_second")
        samples_per_second = (
            iterations_per_second * configuration.execution.batch_size
            if iterations_per_second is not None
            else None
        )
        return [
            self._metric(
                name="throughput_samples_per_second",
                display_name="Sample Throughput",
                value=samples_per_second,
                unit="samples/s",
                kind=MetricKind.DERIVED,
                higher_is_better=True,
                assumptions=["Iteration throughput multiplied by configured batch size."],
            )
        ]

    def _resource_metrics(self, observation_samples: Mapping[str, Sequence[float]]) -> list[Metric]:
        """Build resource metrics from values collected in a single run scan."""
        memory_samples = observation_samples["memory"]
        cpu_samples = observation_samples["cpu"]
        gpu_samples = observation_samples["gpu"]
        return [
            *self._sample_metrics(
                prefix="memory",
                display_prefix="Memory Usage",
                unit="bytes",
                samples=memory_samples,
                higher_is_better=False,
            ),
            *self._sample_metrics(
                prefix="cpu_utilization",
                display_prefix="CPU Utilization",
                unit="percent",
                samples=cpu_samples,
                higher_is_better=None,
            ),
            *self._sample_metrics(
                prefix="gpu_utilization",
                display_prefix="GPU Utilization",
                unit="percent",
                samples=gpu_samples,
                higher_is_better=None,
            ),
        ]

    def _flops_metrics(
        self,
        statistics: Mapping[str, float],
        runs: Sequence[ExecutionResult],
        workload: ModelMetadata | None,
        observed_operation_counts: Sequence[float],
    ) -> list[Metric]:
        operation_count = self._operation_count(runs, workload, observed_operation_counts)
        throughput = statistics.get("throughput_iterations_per_second")
        estimated_flops = (
            operation_count * throughput
            if operation_count is not None and throughput is not None
            else None
        )
        return [
            self._metric(
                name="estimated_flops_per_second",
                display_name="Estimated FLOPS",
                value=estimated_flops,
                unit="FLOP/s",
                kind=(
                    MetricKind.ESTIMATED if estimated_flops is not None else MetricKind.UNAVAILABLE
                ),
                higher_is_better=True,
                assumptions=[
                    "Uses workload flops_estimate, twice MAC count, "
                    "or backend-reported operation count."
                ],
            )
        ]

    def _sample_metrics(
        self,
        *,
        prefix: str,
        display_prefix: str,
        unit: str,
        samples: Sequence[float],
        higher_is_better: bool | None,
    ) -> list[Metric]:
        if not samples:
            return [
                self._metric(
                    name=f"{prefix}_mean_{unit}",
                    display_name=f"Mean {display_prefix}",
                    value=None,
                    unit=unit,
                    kind=MetricKind.UNAVAILABLE,
                    higher_is_better=higher_is_better,
                    assumptions=["No compatible backend observations were reported."],
                ),
                self._metric(
                    name=f"{prefix}_max_{unit}",
                    display_name=f"Maximum {display_prefix}",
                    value=None,
                    unit=unit,
                    kind=MetricKind.UNAVAILABLE,
                    higher_is_better=higher_is_better,
                    assumptions=["No compatible backend observations were reported."],
                ),
            ]

        return [
            self._metric(
                name=f"{prefix}_mean_{unit}",
                display_name=f"Mean {display_prefix}",
                value=fmean(samples),
                unit=unit,
                kind=MetricKind.MEASURED,
                higher_is_better=higher_is_better,
            ),
            self._metric(
                name=f"{prefix}_max_{unit}",
                display_name=f"Maximum {display_prefix}",
                value=max(samples),
                unit=unit,
                kind=MetricKind.MEASURED,
                higher_is_better=higher_is_better,
            ),
        ]

    def _summary(
        self,
        *,
        session_id: str,
        configuration: Configuration,
        hardware: HardwareProfile,
        workload: ModelMetadata | None,
        statistics: Mapping[str, float],
        metrics: Sequence[Metric],
        failure_message: str | None,
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "status": "failed" if failure_message is not None else "success",
            "backend": configuration.backend.name,
            "device": configuration.backend.device,
            "precision": configuration.execution.precision,
            "batch_size": configuration.execution.batch_size,
            "measurement_count": int(statistics.get("count", 0.0)),
            "hardware": hardware.summary(),
            "workload": workload.summary() if workload is not None else None,
            "primary_metrics": {
                metric.name: metric.value
                for metric in metrics
                if metric.name in self._primary_names()
            },
            "resource_metrics": {
                metric.name: metric.value
                for metric in metrics
                if metric.name.startswith(("memory_", "cpu_utilization_", "gpu_utilization_"))
            },
            "assumptions": sorted(
                {assumption for metric in metrics for assumption in metric.assumptions}
            ),
        }

    @staticmethod
    def _primary_names() -> set[str]:
        return {"latency_mean_seconds", "throughput_iterations_per_second"}

    @staticmethod
    def _collect_observation_samples(runs: Sequence[ExecutionResult]) -> dict[str, list[float]]:
        """Collect all known observation categories with one pass over benchmark runs."""
        keys_by_category = {
            "memory": (
                "memory_peak_bytes",
                "peak_memory_bytes",
                "memory_usage_bytes",
                "memory_bytes",
                "process_memory_bytes",
                "rss_bytes",
            ),
            "cpu": ("cpu_utilization_percent", "cpu_percent", "process_cpu_percent"),
            "gpu": ("gpu_utilization_percent", "gpu_percent"),
            "operations": ("flop_count", "flops_estimate", "flops", "operation_count", "macs"),
        }
        samples: dict[str, list[float]] = {category: [] for category in keys_by_category}
        for run in runs:
            observations = run.observations
            for category, keys in keys_by_category.items():
                for key in keys:
                    value = observations.get(key)
                    if isinstance(value, int | float):
                        samples[category].append(float(value))
                        break
        return samples

    @staticmethod
    def _collect_observation_values(
        runs: Sequence[ExecutionResult],
        keys: Sequence[str],
    ) -> list[float]:
        values: list[float] = []
        for run in runs:
            for key in keys:
                value = run.observations.get(key)
                if isinstance(value, int | float):
                    values.append(float(value))
                    break
        return values

    @staticmethod
    def _operation_count(
        runs: Sequence[ExecutionResult],
        workload: ModelMetadata | None,
        observed_operation_counts: Sequence[float] | None = None,
    ) -> float | None:
        if workload is not None:
            if workload.flops_estimate is not None:
                return float(workload.flops_estimate)
            if workload.macs is not None:
                return float(workload.macs * 2)
        if observed_operation_counts is not None:
            return observed_operation_counts[0] if observed_operation_counts else None
        observations = CoreMetricsEngine._collect_observation_values(
            runs,
            ("flop_count", "flops_estimate", "flops", "operation_count", "macs"),
        )
        return observations[0] if observations else None

    @staticmethod
    def _metric(
        *,
        name: str,
        display_name: str,
        value: float | int | str | None,
        unit: str,
        kind: MetricKind,
        higher_is_better: bool | None,
        assumptions: list[str] | None = None,
    ) -> Metric:
        return Metric(
            name=name,
            display_name=display_name,
            value=value,
            unit=unit,
            kind=kind if value is not None else MetricKind.UNAVAILABLE,
            source=METRIC_SOURCE,
            higher_is_better=higher_is_better,
            assumptions=assumptions or [],
        )
