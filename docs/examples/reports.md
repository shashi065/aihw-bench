# Example: Reports

Reports are generated from finalized sessions. The report service writes artifacts with checksums and session metadata.

```bash
aihw-bench report SESSION_ID --format json --format html --output-dir reports
```

For automation, prefer JSON or CSV. For review, prefer Markdown or HTML.

HTML reports can include visualization components produced by the visualization service when the session contains the required metrics and run data.
