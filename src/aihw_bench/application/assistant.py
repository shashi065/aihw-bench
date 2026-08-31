"""Grounded local benchmark intelligence with optional AI-provider extension points."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, stdev
from typing import Protocol

from aihw_bench.domain.models import BenchmarkSession, Configuration, Metric

ASSISTANT_DOCUMENTATION = "docs/user-guide/assistant.md"
MINIMUM_VARIANCE_SAMPLES = 3
ANOMALY_VARIATION_THRESHOLD = 0.2
REGRESSION_THRESHOLD = 0.05


@dataclass(frozen=True, slots=True)
class AssistantInsight:
    """One grounded assistant finding with a confidence label and source metric."""

    category: str
    summary: str
    recommendation: str
    confidence: str = "high"
    metric: str | None = None


@dataclass(frozen=True, slots=True)
class AssistantResponse:
    """Explainable benchmark intelligence for a session or session pair."""

    summary: str
    insights: tuple[AssistantInsight, ...]
    recommended_configuration: Configuration

    def to_markdown(self) -> str:
        """Render a portable assistant report suitable for tickets or reports."""
        lines = ["# AIHW-Bench Assistant Report", "", self.summary, "", "## Findings", ""]
        lines.extend(
            f"- **{insight.category}:** {insight.summary} Recommendation: {insight.recommendation}"
            for insight in self.insights
        )
        lines.extend(["", "## Recommended Configuration", "", "```yaml"])
        lines.append(self.recommended_configuration.to_resolved_yaml().rstrip())
        lines.extend(["```", ""])
        return "\n".join(lines)


class BenchmarkIntelligenceProvider(Protocol):
    """Optional provider protocol for an externally hosted AI explanation service."""

    def explain(
        self, session: BenchmarkSession, baseline: BenchmarkSession | None = None
    ) -> AssistantResponse: ...


class BenchmarkAssistant:
    """Generate deterministic, metric-grounded benchmark intelligence locally."""

    def explain(
        self,
        session: BenchmarkSession,
        baseline: BenchmarkSession | None = None,
    ) -> AssistantResponse:
        """Explain results, anomalies, hardware deltas, and optimization opportunities."""
        metrics = _metrics(session.metrics)
        insights = [*self._anomalies(session, metrics), *self._optimizations(session, metrics)]
        if baseline is not None:
            insights.extend(self._comparison(session, baseline, metrics))
        summary = self._summary(session, metrics, baseline)
        return AssistantResponse(
            summary=summary,
            insights=tuple(insights)
            or (
                AssistantInsight(
                    "status",
                    "No notable anomalies were detected.",
                    "Use this session as a stable baseline.",
                ),
            ),
            recommended_configuration=self._recommend_configuration(session, metrics),
        )

    @staticmethod
    def _summary(
        session: BenchmarkSession, metrics: dict[str, float], baseline: BenchmarkSession | None
    ) -> str:
        latency = metrics.get("latency_mean_seconds")
        throughput = metrics.get("throughput_iterations_per_second")
        base = (
            f"Session {session.session_id} ran on {session.configuration.backend.name}/"
            f"{session.configuration.backend.device}."
        )
        performance = (
            f" Mean latency was {latency:g}s."
            if latency is not None
            else " No mean latency was recorded."
        )
        performance += (
            f" Throughput was {throughput:g} iterations/s." if throughput is not None else ""
        )
        return base + performance + (" A baseline comparison is included." if baseline else "")

    @staticmethod
    def _anomalies(session: BenchmarkSession, metrics: dict[str, float]) -> list[AssistantInsight]:
        findings: list[AssistantInsight] = []
        durations = [run.duration_seconds for run in session.runs if run.duration_seconds > 0]
        if (
            len(durations) >= MINIMUM_VARIANCE_SAMPLES
            and fmean(durations) > 0
            and stdev(durations) / fmean(durations) > ANOMALY_VARIATION_THRESHOLD
        ):
            findings.append(
                AssistantInsight(
                    "anomaly",
                    "Iteration latency is variable (coefficient of variation above 20%).",
                    "Increase warmup iterations and investigate competing host activity.",
                    metric="latency_mean_seconds",
                )
            )
        if session.diagnostics:
            findings.append(
                AssistantInsight(
                    "anomaly",
                    f"Session contains {len(session.diagnostics)} diagnostic message(s).",
                    "Review diagnostics before treating this result as a release baseline.",
                    confidence="high",
                )
            )
        if metrics.get("memory_max_bytes", 0) > metrics.get("memory_mean_bytes", 0) * 2 > 0:
            findings.append(
                AssistantInsight(
                    "anomaly",
                    "Peak memory is more than twice mean memory.",
                    "Inspect allocation spikes or reduce batch size.",
                    metric="memory_max_bytes",
                )
            )
        return findings

    @staticmethod
    def _optimizations(
        session: BenchmarkSession, metrics: dict[str, float]
    ) -> list[AssistantInsight]:
        findings: list[AssistantInsight] = []
        execution = session.configuration.execution
        if execution.warmup_iterations == 0:
            findings.append(
                AssistantInsight(
                    "optimization",
                    "No warmup iterations are configured.",
                    "Use at least one warmup iteration to reduce cold-start distortion.",
                )
            )
        if execution.batch_size == 1 and session.configuration.backend.device != "cpu":
            findings.append(
                AssistantInsight(
                    "optimization",
                    "Accelerator run uses batch size 1.",
                    "Evaluate larger batches while monitoring memory headroom.",
                )
            )
        if metrics.get("throughput_iterations_per_second", 0) == 0:
            findings.append(
                AssistantInsight(
                    "optimization",
                    "No positive throughput was recorded.",
                    "Verify successful measurements and backend observations.",
                )
            )
        return findings

    @staticmethod
    def _comparison(
        session: BenchmarkSession, baseline: BenchmarkSession, metrics: dict[str, float]
    ) -> list[AssistantInsight]:
        baseline_metrics = _metrics(baseline.metrics)
        findings: list[AssistantInsight] = []
        for name in ("latency_mean_seconds", "throughput_iterations_per_second"):
            if name not in metrics or name not in baseline_metrics or baseline_metrics[name] == 0:
                continue
            change = (metrics[name] - baseline_metrics[name]) / baseline_metrics[name]
            worse = (name.startswith("latency") and change > REGRESSION_THRESHOLD) or (
                name.startswith("throughput") and change < -REGRESSION_THRESHOLD
            )
            if worse:
                findings.append(
                    AssistantInsight(
                        "hardware comparison",
                        f"{name} changed by {change:+.1%} versus {baseline.session_id}.",
                        "Confirm hardware, driver, precision, and batch-size parity "
                        "before accepting the regression.",
                        metric=name,
                    )
                )
        if session.hardware.summary() != baseline.hardware.summary():
            findings.append(
                AssistantInsight(
                    "hardware comparison",
                    "Hardware summaries differ between compared sessions.",
                    "Treat the comparison as cross-hardware rather than a direct regression test.",
                    confidence="medium",
                )
            )
        return findings

    @staticmethod
    def _recommend_configuration(
        session: BenchmarkSession, metrics: dict[str, float]
    ) -> Configuration:
        execution = session.configuration.execution
        updates: dict[str, int] = {}
        if execution.warmup_iterations == 0:
            updates["warmup_iterations"] = 1
        if (
            metrics.get("memory_max_bytes", 0)
            and metrics.get("memory_mean_bytes", 0) * 2 < metrics["memory_max_bytes"]
        ):
            updates["batch_size"] = max(1, execution.batch_size // 2)
        return session.configuration.model_copy(
            update={"execution": execution.model_copy(update=updates)}
        )


def _metrics(metrics: list[Metric]) -> dict[str, float]:
    return {
        metric.name: float(metric.value)
        for metric in metrics
        if isinstance(metric.value, int | float)
    }
