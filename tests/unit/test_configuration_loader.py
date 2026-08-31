import json
from pathlib import Path

import pytest

from aihw_bench.domain.errors import ConfigurationError
from aihw_bench.infrastructure.configuration import load_configuration

DEFAULT_ITERATIONS = 5
ENV_ITERATIONS = 7
FILE_WARMUP = 2
PROFILE_ITERATIONS = 2
JSON_ITERATIONS = 2


def test_load_configuration_uses_default_values() -> None:
    config = load_configuration(env={})

    assert config.profile == "default"
    assert config.backend.name == "reference"
    assert config.execution.iterations == DEFAULT_ITERATIONS
    assert config.metrics.enabled == ["latency", "throughput"]


def test_load_configuration_applies_file_env_and_cli_precedence(tmp_path: Path) -> None:
    config_file = tmp_path / "benchmark.yaml"
    config_file.write_text(
        """
backend:
  name: file-backend
execution:
  iterations: 3
  warmup_iterations: 2
""",
        encoding="utf-8",
    )

    config = load_configuration(
        config_path=config_file,
        env={
            "AIHW_BENCH_EXECUTION__ITERATIONS": "7",
            "AIHW_BENCH_BACKEND__DEVICE": "gpu0",
        },
        cli_overrides={"backend": {"name": "cli-backend"}},
    )

    assert config.backend.name == "cli-backend"
    assert config.backend.device == "gpu0"
    assert config.execution.iterations == ENV_ITERATIONS
    assert config.execution.warmup_iterations == FILE_WARMUP
    assert [source.kind for source in config.sources] == ["default", "file", "environment", "cli"]


def test_load_configuration_resolves_profile_inheritance(tmp_path: Path) -> None:
    config_file = tmp_path / "profiles.yaml"
    config_file.write_text(
        """
profiles:
  base:
    execution:
      iterations: 10
      warmup_iterations: 1
  ci:
    extends: base
    execution:
      iterations: 2
    reports:
      formats: ["json"]
""",
        encoding="utf-8",
    )

    config = load_configuration(config_path=config_file, profile="ci", env={})

    assert config.profile == "ci"
    assert config.execution.iterations == PROFILE_ITERATIONS
    assert config.execution.warmup_iterations == 1
    assert config.reports.formats == ["json"]


def test_load_configuration_rejects_profile_cycles(tmp_path: Path) -> None:
    config_file = tmp_path / "profiles.yaml"
    config_file.write_text(
        """
profiles:
  a:
    extends: b
  b:
    extends: a
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="cycle"):
        load_configuration(config_path=config_file, profile="a", env={})


def test_load_configuration_rejects_unsupported_format(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("backend = 'x'", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Unsupported"):
        load_configuration(config_path=config_file, env={})


def test_load_configuration_reads_json_files(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"execution": {"iterations": 2}, "backend": {"device": "cpu"}}),
        encoding="utf-8",
    )

    config = load_configuration(config_path=config_file, env={})

    assert config.execution.iterations == JSON_ITERATIONS
    assert config.backend.device == "cpu"


def test_load_configuration_rejects_missing_files(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="does not exist"):
        load_configuration(config_path=tmp_path / "missing.yaml", env={})


def test_load_configuration_rejects_non_mapping_files(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("- not\n- mapping\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="mapping"):
        load_configuration(config_path=config_file, env={})


def test_load_configuration_rejects_malformed_json(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text("{bad json", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="could not be read"):
        load_configuration(config_path=config_file, env={})


def test_load_configuration_rejects_invalid_profiles_key(tmp_path: Path) -> None:
    config_file = tmp_path / "profiles.yaml"
    config_file.write_text("profiles: invalid\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Profiles"):
        load_configuration(config_path=config_file, env={})


def test_load_configuration_rejects_missing_profile(tmp_path: Path) -> None:
    config_file = tmp_path / "profiles.yaml"
    config_file.write_text(
        "profiles:\n  ci:\n    execution:\n      iterations: 1\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="does not exist"):
        load_configuration(config_path=config_file, profile="missing", env={})


def test_load_configuration_rejects_non_mapping_profile(tmp_path: Path) -> None:
    config_file = tmp_path / "profiles.yaml"
    config_file.write_text("profiles:\n  bad: value\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="profile must be a mapping"):
        load_configuration(config_path=config_file, profile="bad", env={})


def test_load_configuration_rejects_non_string_profile_parent(tmp_path: Path) -> None:
    config_file = tmp_path / "profiles.yaml"
    config_file.write_text("profiles:\n  child:\n    extends: [base]\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="extends"):
        load_configuration(config_path=config_file, profile="child", env={})


def test_load_configuration_rejects_environment_path_conflicts() -> None:
    env = {
        "AIHW_BENCH_BACKEND": "reference",
        "AIHW_BENCH_BACKEND__DEVICE": "cpu",
    }

    with pytest.raises(ConfigurationError, match="path conflicts"):
        load_configuration(env=env)


def test_load_configuration_keeps_unparseable_environment_values() -> None:
    config = load_configuration(env={"AIHW_BENCH_TAGS__NOTE": "[unterminated"})

    assert config.tags["note"] == "[unterminated"
