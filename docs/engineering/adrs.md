# Architecture Decision Records

## ADR-0001: Use Clean Architecture

Status: Accepted

Context: The framework must support many hardware, runtime, storage, report, and visualization implementations without coupling domain logic to vendor-specific dependencies.

Decision: Use Clean Architecture with dependency direction from presentation to application to domain ports, with infrastructure implementing those ports.

Consequences: Adapters remain replaceable, tests can run without heavy dependencies, and public domain models stay stable. The project must enforce import boundaries through review and tests.

## ADR-0002: Keep Heavy AI Runtime Dependencies Optional

Status: Accepted

Context: PyTorch, ONNX Runtime, TensorFlow Lite, CUDA SDKs, simulator binaries, and vendor tools can be large, platform-specific, or unavailable.

Decision: Core installation provides framework contracts and CPU-safe functionality. Runtime-specific adapters are installed through extras or third-party plugins.

Consequences: `pip install aihw-bench` remains lightweight. Runtime adapters must provide clear diagnostics when optional dependencies are missing.

## ADR-0003: Use Entry Points for Plugin Discovery

Status: Accepted

Context: Plugin authors need a standard Python packaging mechanism that works across PyPI, internal package indexes, and editable installs.

Decision: Discover plugins through the `aihw_bench.plugins` entry point group.

Consequences: Plugins can be installed independently. The core loader must validate plugin metadata and isolate plugin errors from unrelated functionality.

## ADR-0004: Store Sessions as Immutable Artifacts

Status: Accepted

Context: Benchmark comparison and publication require reproducibility and traceability.

Decision: Persist benchmark sessions as immutable directories containing configuration, metadata, raw observations, computed metrics, and report artifacts.

Consequences: Historical comparisons are reliable. Storage growth is managed through explicit retention policies rather than mutation.

## ADR-0005: Use Typer and Rich for CLI

Status: Accepted

Context: The CLI must be approachable for humans while remaining scriptable.

Decision: Use Typer for typed command definitions and Rich for tables, progress, and styled diagnostics.

Consequences: CLI code stays concise and testable. Machine-readable modes must avoid Rich formatting.
