# FAQ

## Is this ready for production benchmarking?

The repository has production-oriented foundations through Milestone 11, including benchmark execution, model support, backends, metrics, reporting, visualization, CLI, plugins, tests, and documentation. Host-specific benchmark accuracy still depends on the selected backend, model runtime, hardware stability, and configuration discipline.

## Why are PyTorch and ONNX Runtime optional?

The core package must remain lightweight and installable on machines that do not have accelerator runtimes or vendor SDKs. Backend support is provided through extras and plugins.

## Will simulator and FPGA workflows be supported?

Yes. The architecture includes simulator and embedded execution adapters. Those integrations belong to later milestones and should arrive as dedicated backends or plugins rather than changes to the core benchmark engine.

## Which report formats are implemented?

JSON, CSV, Markdown, and HTML reports are implemented. Reports are generated from finalized benchmark sessions and can include visualization components.

## How do I keep tests reproducible?

Use fake backends, scripted timing, temporary session stores, and deterministic input data. The test suite enforces at least 95% coverage and avoids requiring specific GPU hardware.
