# Dashboard

AIHW-Bench v2.0 generates a static responsive dashboard from sessions stored on disk. It does not start a server or upload session data.

```bash
aihw-bench dashboard --storage-root .aihw-bench/sessions --output-dir dashboard
```

The generated dashboard uses packaged CSS/JavaScript assets and renders session data through DOM text APIs rather than HTML interpolation. It loads a bounded recent history page (200 sessions by default) so a large history is not embedded unboundedly. Damaged session files are skipped without preventing valid-session rendering.

Interactive charts use the pinned Plotly 2.35.2 CDN when it is reachable. The dashboard remains usable for browsing, filtering, and exporting when Plotly is unavailable; charts are simply unavailable. Its Content Security Policy permits scripts only from the dashboard assets and that pinned Plotly origin. For fully offline controlled deployments, provide a vetted local Plotly asset and adjust the generated CSP/source as part of your deployment process.

The dashboard includes benchmark history, hardware comparison, filters, search, report/capability inspection, JSON/CSV export, dark mode, and responsive layout. Treat generated dashboards as local artifacts and keep stored sessions from untrusted parties isolated.
