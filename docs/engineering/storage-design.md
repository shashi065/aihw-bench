# Storage Design

## Storage Model

The first production storage implementation is a filesystem-backed session store. Database storage is intentionally deferred until multi-user server workflows exist.

## Session Directory Layout

```text
.aihw-bench/
  sessions/
    2026-07-29T120000Z_01HX.../
      session.json
      config.resolved.yaml
      observations.jsonl
      metrics.json
      system.json
      artifacts/
        report.html
        report.md
        report.csv
```

## Immutability

Session records are immutable after completion. Additional derived artifacts may be added under `artifacts/`, but existing canonical data files are not modified.

## File Formats

- `session.json`: normalized session metadata and references.
- `config.resolved.yaml`: effective configuration after precedence resolution.
- `observations.jsonl`: raw timing and profiler observations.
- `metrics.json`: computed metrics with units, sources, and assumptions.
- `system.json`: hardware, OS, Python, package, and backend metadata.

## Retention

Retention policies are explicit commands or configuration settings. The store never removes historical sessions implicitly.

## Future Database Support

A database-backed store may be added behind the `SessionStore` port for multi-user dashboards. Candidate implementations include SQLite for local dashboards and PostgreSQL for hosted services.
