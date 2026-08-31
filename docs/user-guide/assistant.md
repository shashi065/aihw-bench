# Local Benchmark Analysis Assistant

AIHW-Bench v2.0 includes a deterministic **local benchmark analysis assistant**. It analyzes recorded metrics, execution samples, hardware summaries, diagnostics, and an optional baseline session. It does not send sessions, credentials, or hardware information to an external service. It is not an LLM.

## Supported analysis

- Explain observed latency and throughput.
- Compare matching metrics with an optional baseline.
- Flag variance, diagnostics, and memory-spike anomalies.
- Recommend warmup, batch-size, and validation changes based on recorded evidence.
- Produce a summary and portable Markdown report.

## Limitations and extension point

Recommendations are deterministic rules over the captured session; they cannot discover unrecorded system state or guarantee performance gains. `BenchmarkIntelligenceProvider` is an extension protocol for a future authenticated provider plugin. Such a provider is not included in v2.0.0; any provider must define its data handling and evaluation policy.

## CLI

```bash
aihw-bench assistant SESSION_ID --storage-root .aihw-bench/sessions
aihw-bench assistant CANDIDATE --baseline BASELINE --output-dir reports
```
