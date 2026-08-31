# Enterprise Foundations

AIHW-Bench v1.5 adds local-first primitives for governed benchmark operations without requiring a cloud account or new runtime service.

## Workspaces and projects

`WorkspaceManager` stores named YAML workspace profiles and project configurations. A project selects a profile, then its configuration overrides profile defaults. Use this for shared backend, reporting, and execution policy.

## History database and comparisons

`SqliteHistoryStore` indexes immutable sessions in a local SQLite database and supports backend/device filters. `ResultComparator` compares numeric metrics that both sessions expose. Existing filesystem session storage remains the durable source of truth.

## Artifact management

Use the existing `FilesystemSessionStore.store_artifact()` interface as the artifact catalog: it copies an artifact into the session workspace, records integrity metadata, and updates the manifest.

## Plugin marketplace foundation

`PluginMarketplace` manages a versioned local JSON index of `MarketplacePlugin` metadata. It supports publish and search only; plugin installation remains an explicit user-controlled packaging operation.

## Remote execution

`RemoteBenchmarkRequest` and `RemoteBenchmarkAgent` define a transport-neutral handoff. Deployers provide an authenticated agent implementation (for example, mTLS or a job queue); AIHW-Bench does not embed credentials or network policy.

## Scheduling

`BenchmarkSchedule` is a pollable, interval-based schedule definition. A runner calls `is_due()` and submits work through the selected local or remote execution path. Persist schedule definitions in project/workspace configuration or your deployment scheduler.

## Example

```python
from pathlib import Path
from aihw_bench import WorkspaceManager, WorkspaceProfile, ProjectConfiguration
from aihw_bench.infrastructure.storage import SqliteHistoryStore

workspace = WorkspaceManager(Path(".aihw-bench/workspace"))
workspace.save_profile(WorkspaceProfile("shared", {"backend": {"name": "reference"}}))
workspace.save_project(ProjectConfiguration("vision", "shared", {"execution": {"iterations": 20}}))
configuration = workspace.resolve("vision")
history = SqliteHistoryStore(Path(".aihw-bench/history.db"))
```
