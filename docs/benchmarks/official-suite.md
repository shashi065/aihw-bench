# Official Benchmark Suite

AIHW-Bench v2.0.0 includes ten versioned, reproducible benchmark contracts. The suite deliberately ships deterministic synthetic input manifests rather than redistributing third-party datasets or model weights. This permits reproducible framework, runtime, and hardware comparisons in offline CI and lab environments. Accuracy-quality metrics are recorded by an integrated runtime or model plugin; the included **synthetic baselines** validate suite plumbing only and use `0.0` for such metrics.

## Reproducibility

Each workload has a fixed ID, input shape, sample count, and seed. `aihw-bench suite materialize` writes one JSON manifest per workload. The manifest lists per-sample seeds and carries a SHA-256 checksum. `aihw-bench suite baselines` writes deterministic reference-backend baseline results.

| Benchmark | Task | Input contract | Samples | Primary quality metric |
| --- | --- | --- | ---: | --- |
| Image Classification | Classification | `1×3×224×224` | 32 | Top-1 accuracy |
| Object Detection | Detection | `1×3×640×640` | 16 | mAP@0.50 |
| Semantic Segmentation | Segmentation | `1×3×512×512` | 16 | Mean IoU |
| LLM Generation | Text generation | `1×128` tokens | 32 | Tokens/s |
| Vision Transformer | Classification | `1×3×224×224` | 32 | Top-1 accuracy |
| CNN | Classification | `1×3×224×224` | 32 | Top-1 accuracy |
| Audio Classification | Classification | `1×1×16000` | 32 | Accuracy |
| Speech Recognition | Transcription | `1×1×16000` | 16 | Word error rate |
| Embedded AI | Classification | `1×3×96×96` | 32 | Top-1 accuracy |
| TinyML | Classification | `1×1×128` | 64 | Accuracy |

## CLI

```bash
aihw-bench suite list
aihw-bench suite materialize --output-dir benchmarks
aihw-bench suite materialize --benchmark tinyml --output-dir benchmarks
aihw-bench suite baselines --output-dir benchmarks
```

## Python API

```python
from pathlib import Path
from aihw_bench import OfficialBenchmarkSuite

suite = OfficialBenchmarkSuite()
suite.materialize_all_datasets(Path("benchmarks"))
suite.write_baselines(Path("benchmarks/official-baselines.json"))
```

The contracts are workload and runtime neutral. The included results are **reference fixtures**, not universal real-device performance measurements. Real hardware performance, accuracy, energy, thermals, and driver-specific behavior require executing a compatible workload/runtime on the target hardware under a documented methodology. Pair a manifest with a supported model loader/backend or a plugin to measure actual model accuracy and device performance.
