# Model Support

Milestone 3 adds a model-loading layer that keeps runtime-specific dependencies outside the domain layer.

## Supported Loaders

- PyTorch and TorchScript via the `pytorch` optional extra.
- ONNX Runtime via the `onnx` optional extra.
- TensorFlow Lite via the `tflite` optional extra when the platform runtime is available.

## Public API

The main entry points are exposed from `aihw_bench.infrastructure.models` and `aihw_bench.domain.model_support`.

```python
from pathlib import Path

from aihw_bench.domain.model_support import ModelLoadRequest
from aihw_bench.infrastructure.models import ModelLoaderRegistry

registry = ModelLoaderRegistry()
loaded = registry.load(ModelLoadRequest(source=Path("model.onnx"), name="demo-model"))

print(loaded.metadata.framework)
print(loaded.metadata.input_shapes)
```

## Metadata

Model metadata records:

- model identity and framework
- tensor shape information
- supported precision where detectable
- supported batch sizes where detectable
- parameter counts where available
- file size and custom metadata

## Benchmark Integration

`BenchmarkService` can resolve a configured workload source through an injected model catalog before benchmark execution starts. This keeps model loading optional and testable while letting the benchmark engine record the loaded metadata in sessions.

## Failure Handling

Model loading failures raise structured AIHW-Bench exceptions with cause, suggested action, and documentation links. Unsupported formats, missing files, invalid graphs, and missing runtime dependencies are reported explicitly.