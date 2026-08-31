"""Jinja templates used by built-in report generators."""

HTML_REPORT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>AIHW-Bench Report - {{ view.session.session_id }}</title>
  {% if view.charts %}
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  {% endif %}
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; color: #1f2937; }
    h1, h2 { color: #111827; }
    table { border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }
    th, td { border: 1px solid #d1d5db; padding: 0.5rem; text-align: left; }
    th { background: #f3f4f6; }
    code { background: #f3f4f6; padding: 0.1rem 0.25rem; }
  </style>
</head>
<body>
  <h1>AIHW-Bench Report</h1>
  <p><strong>Session:</strong> {{ view.session.session_id }}</p>
  <p><strong>Status:</strong> {{ view.session.status }}</p>
  <h2>Benchmark Summary</h2>
  <table>
    <tbody>
    {% for key, value in view.benchmark_summary.items() %}
      <tr><th>{{ key }}</th><td>{{ value }}</td></tr>
    {% endfor %}
    </tbody>
  </table>
  <h2>Metrics</h2>
  <table>
    <thead>
      <tr><th>Name</th><th>Value</th><th>Unit</th><th>Kind</th><th>Source</th></tr>
    </thead>
    <tbody>
    {% for metric in view.metrics %}
      <tr>
        <td><code>{{ metric.name }}</code></td>
        <td>{{ metric.value }}</td>
        <td>{{ metric.unit }}</td>
        <td>{{ metric.kind }}</td>
        <td>{{ metric.source }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% if view.charts %}
  <h2>Charts</h2>
  {% for chart in view.charts %}
    {{ chart.html | safe }}
  {% endfor %}
  {% endif %}
  <h2>Hardware Summary</h2>
  <pre>{{ view.hardware_summary | tojson(indent=2) }}</pre>
  <h2>Model Summary</h2>
  <pre>{{ view.model_summary | tojson(indent=2) }}</pre>
  <h2>Diagnostics</h2>
  <pre>{{ view.diagnostics | tojson(indent=2) }}</pre>
</body>
</html>
"""

MARKDOWN_HEADER = "# AIHW-Bench Report"
