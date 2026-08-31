# CLI Specification

## Design Principles

- Human-readable by default.
- Machine-readable with explicit `--output json` or export commands.
- Stable exit codes.
- Clear diagnostics for missing optional dependencies.
- Rich tables and progress displays only when attached to an interactive terminal.

## Commands

### `aihw-bench benchmark`

Runs benchmark workloads and stores a benchmark session.

Core options:

- `--config PATH`
- `--model PATH_OR_ID`
- `--backend NAME`
- `--device DEVICE`
- `--batch-size INTEGER`
- `--precision NAME`
- `--warmup INTEGER`
- `--iterations INTEGER`
- `--output-dir PATH`
- `--report FORMAT`

### `aihw-bench profile`

Runs a workload with selected profilers and emits profiler artifacts.

### `aihw-bench compare`

Compares two or more benchmark sessions.

### `aihw-bench report`

Generates reports from an existing session.

### `aihw-bench dashboard`

Launches a local dashboard for browsing sessions. This command is planned after the filesystem session store and report generation are stable.

### `aihw-bench export`

Exports session or comparison data as JSON, CSV, Markdown, or HTML.

### `aihw-bench doctor`

Checks installation health, optional dependencies, plugin validity, backend availability, and writable storage paths.

### `aihw-bench version`

Prints package, Python, platform, and plugin API versions.

## Exit Codes

- `0`: success.
- `1`: unexpected internal error.
- `2`: invalid CLI usage or configuration.
- `3`: backend unavailable or unsupported capability.
- `4`: benchmark execution failed.
- `5`: report or export generation failed.
- `6`: plugin validation failed.

## Output Modes

- `table`: default human-readable Rich output.
- `json`: structured output for automation.
- `quiet`: only essential output.
- `verbose`: diagnostic output.
