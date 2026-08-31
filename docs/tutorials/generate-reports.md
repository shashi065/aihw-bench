# Tutorial: Generate Reports

AIHW-Bench reports are generated from finalized session records.

## Supported Formats

- JSON for automation and archival.
- CSV for spreadsheets and simple tabular analysis.
- Markdown for lightweight review.
- HTML for shareable human-readable reports.

## Generate Reports For A Stored Session

```bash
aihw-bench report SESSION_ID \
  --format json \
  --format csv \
  --format markdown \
  --format html \
  --output-dir reports
```

## Export Session Data

The export command always writes canonical session JSON and can also render reports.

```bash
aihw-bench export SESSION_ID --format markdown --format html --output-dir artifacts
```

## Report Contents

Reports include metadata, benchmark summary, hardware summary, model summary, metrics, run summaries, diagnostics, and visualization components when charts can be built for the session.
