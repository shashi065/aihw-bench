from __future__ import annotations

import json

import pytest

from aihw_bench.application import OfficialBenchmarkSuite
from aihw_bench.domain.errors import ValidationError

EXPECTED_SUITE_SIZE = 10
EXPECTED_CNN_SAMPLES = 32


def test_official_suite_includes_every_announced_category() -> None:
    definitions = OfficialBenchmarkSuite().definitions()

    assert len(definitions) == EXPECTED_SUITE_SIZE
    assert {definition.identifier for definition in definitions} >= {
        "image-classification",
        "object-detection",
        "semantic-segmentation",
        "llm-generation",
        "vision-transformer",
        "cnn",
        "audio-classification",
        "speech-recognition",
        "embedded-ai",
        "tinyml",
    }


def test_dataset_manifests_are_reproducible(tmp_path) -> None:
    suite = OfficialBenchmarkSuite()
    first = suite.materialize_dataset("cnn", tmp_path / "first")
    second = suite.materialize_dataset("cnn", tmp_path / "second")

    first_payload = json.loads(first.read_text(encoding="utf-8"))
    second_payload = json.loads(second.read_text(encoding="utf-8"))
    assert first_payload == second_payload
    assert len(first_payload["samples"]) == EXPECTED_CNN_SAMPLES
    assert first_payload["sha256"]


def test_baselines_are_stable_and_complete(tmp_path) -> None:
    suite = OfficialBenchmarkSuite()
    path = suite.write_baselines(tmp_path / "baselines.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert len(payload["results"]) == len(suite.definitions())
    assert all(result["backend"] == "reference" for result in payload["results"])


def test_unknown_official_benchmark_is_rejected() -> None:
    with pytest.raises(ValidationError, match="not available"):
        OfficialBenchmarkSuite().definition("unknown")
