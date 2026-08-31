"""Official reproducible benchmark-suite catalogue and deterministic fixtures."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Final

from aihw_bench.domain.errors import ValidationError

SUITE_DOCUMENTATION: Final[str] = "docs/benchmarks/official-suite.md"


@dataclass(frozen=True, slots=True)
class BenchmarkDefinition:
    """One official, runtime-neutral benchmark workload definition."""

    identifier: str
    name: str
    category: str
    task: str
    input_shape: tuple[int, ...]
    sample_count: int
    seed: int
    description: str
    metric: str

    def dataset_manifest(self) -> dict[str, object]:
        """Return a deterministic synthetic-input manifest for this benchmark."""
        samples = [
            {
                "id": f"{self.identifier}-{index:05d}",
                "seed": self.seed + index,
                "shape": list(self.input_shape),
            }
            for index in range(self.sample_count)
        ]
        payload: dict[str, object] = {
            "schema_version": "1.0",
            "benchmark": self.identifier,
            "task": self.task,
            "generator": "aihw-bench deterministic synthetic inputs",
            "seed": self.seed,
            "input_shape": list(self.input_shape),
            "samples": samples,
        }
        payload["sha256"] = _canonical_digest(payload)
        return payload


@dataclass(frozen=True, slots=True)
class BaselineResult:
    """Reference-backend baseline used to validate suite plumbing, not model accuracy."""

    benchmark: str
    backend: str
    device: str
    batch_size: int
    latency_mean_seconds: float
    throughput_samples_per_second: float
    metric: str
    metric_value: float


OFFICIAL_BENCHMARKS: Final[tuple[BenchmarkDefinition, ...]] = (
    BenchmarkDefinition(
        "image-classification",
        "Image Classification",
        "vision",
        "classification",
        (1, 3, 224, 224),
        32,
        1101,
        "224px image-classification input contract.",
        "top1_accuracy",
    ),
    BenchmarkDefinition(
        "object-detection",
        "Object Detection",
        "vision",
        "detection",
        (1, 3, 640, 640),
        16,
        1201,
        "640px object-detection input contract.",
        "map_50",
    ),
    BenchmarkDefinition(
        "semantic-segmentation",
        "Semantic Segmentation",
        "vision",
        "segmentation",
        (1, 3, 512, 512),
        16,
        1301,
        "512px semantic-segmentation input contract.",
        "mean_iou",
    ),
    BenchmarkDefinition(
        "llm-generation",
        "LLM Generation",
        "language",
        "text-generation",
        (1, 128),
        32,
        1401,
        "Tokenized autoregressive-generation input contract.",
        "tokens_per_second",
    ),
    BenchmarkDefinition(
        "vision-transformer",
        "Vision Transformer",
        "vision",
        "classification",
        (1, 3, 224, 224),
        32,
        1501,
        "Vision Transformer image-token input contract.",
        "top1_accuracy",
    ),
    BenchmarkDefinition(
        "cnn",
        "Convolutional Neural Network",
        "vision",
        "classification",
        (1, 3, 224, 224),
        32,
        1601,
        "CNN image-classification input contract.",
        "top1_accuracy",
    ),
    BenchmarkDefinition(
        "audio-classification",
        "Audio Classification",
        "audio",
        "classification",
        (1, 1, 16000),
        32,
        1701,
        "One-second mono audio input contract at 16 kHz.",
        "accuracy",
    ),
    BenchmarkDefinition(
        "speech-recognition",
        "Speech Recognition",
        "audio",
        "transcription",
        (1, 1, 16000),
        16,
        1801,
        "One-second speech feature input contract at 16 kHz.",
        "word_error_rate",
    ),
    BenchmarkDefinition(
        "embedded-ai",
        "Embedded AI",
        "embedded",
        "classification",
        (1, 3, 96, 96),
        32,
        1901,
        "Embedded vision input contract for constrained accelerators.",
        "top1_accuracy",
    ),
    BenchmarkDefinition(
        "tinyml",
        "TinyML",
        "embedded",
        "classification",
        (1, 1, 128),
        64,
        2001,
        "Small sensor-window input contract for microcontrollers.",
        "accuracy",
    ),
)

BASELINE_RESULTS: Final[tuple[BaselineResult, ...]] = tuple(
    BaselineResult(
        benchmark=definition.identifier,
        backend="reference",
        device="cpu",
        batch_size=1,
        latency_mean_seconds=round(0.001 + (index * 0.0001), 7),
        throughput_samples_per_second=round(1 / (0.001 + (index * 0.0001)), 4),
        metric=definition.metric,
        metric_value=0.0,
    )
    for index, definition in enumerate(OFFICIAL_BENCHMARKS)
)


class OfficialBenchmarkSuite:
    """Discover official workloads and materialize deterministic dataset fixtures."""

    def definitions(self) -> tuple[BenchmarkDefinition, ...]:
        """Return official workloads in stable release order."""
        return OFFICIAL_BENCHMARKS

    def definition(self, identifier: str) -> BenchmarkDefinition:
        """Return one benchmark definition or raise a structured validation error."""
        normalized = identifier.strip().lower()
        for definition in OFFICIAL_BENCHMARKS:
            if definition.identifier == normalized:
                return definition
        raise ValidationError(
            "Official benchmark is not available.",
            cause=f"No official benchmark named {identifier!r} exists.",
            suggestion="Choose a benchmark returned by OfficialBenchmarkSuite.definitions().",
            documentation=SUITE_DOCUMENTATION,
        )

    def materialize_dataset(self, identifier: str, output_dir: Path) -> Path:
        """Write one deterministic dataset manifest and return its path."""
        definition = self.definition(identifier)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{definition.identifier}.dataset.json"
        path.write_text(
            json.dumps(definition.dataset_manifest(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def materialize_all_datasets(self, output_dir: Path) -> tuple[Path, ...]:
        """Write manifests for the full official suite in stable order."""
        return tuple(
            self.materialize_dataset(definition.identifier, output_dir)
            for definition in OFFICIAL_BENCHMARKS
        )

    def baseline_results(self) -> tuple[BaselineResult, ...]:
        """Return immutable reference-backend baseline fixtures."""
        return BASELINE_RESULTS

    def write_baselines(self, output_path: Path) -> Path:
        """Write deterministic reference baseline results."""
        payload = {
            "schema_version": "1.0",
            "results": [asdict(result) for result in BASELINE_RESULTS],
        }
        payload["sha256"] = _canonical_digest(payload)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return output_path


def _canonical_digest(payload: Mapping[str, object]) -> str:
    """Hash a payload before its self-referential checksum is inserted."""
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
