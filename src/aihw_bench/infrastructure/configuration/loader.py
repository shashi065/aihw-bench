"""Configuration loading from defaults, files, environment, and CLI overrides."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError

from aihw_bench.domain.errors import ConfigurationError
from aihw_bench.domain.models import Configuration, ConfigurationSource

ENV_PREFIX = "AIHW_BENCH_"


def load_configuration(
    *,
    config_path: Path | None = None,
    env: Mapping[str, str] | None = None,
    cli_overrides: Mapping[str, Any] | None = None,
    profile: str | None = None,
    defaults: Configuration | None = None,
) -> Configuration:
    """Load and resolve configuration with deterministic precedence.

    Precedence is CLI, environment, configuration file, then defaults.
    """
    base = (defaults or Configuration()).model_dump(mode="json")
    sources = [ConfigurationSource(name="built-in defaults", kind="default")]

    file_data: dict[str, Any] = {}
    if config_path is not None:
        file_data = _read_config_file(config_path)
        sources.append(
            ConfigurationSource(name=config_path.name, kind="file", path=str(config_path))
        )
        selected_profile = profile or _string_or_none(file_data.get("profile")) or "default"
        file_data = _resolve_profile(file_data, selected_profile)

    env_data = _env_to_mapping(env or os.environ)
    if env_data:
        sources.append(ConfigurationSource(name=ENV_PREFIX.rstrip("_"), kind="environment"))

    cli_data = dict(cli_overrides or {})
    if profile is not None:
        cli_data["profile"] = profile
    if cli_data:
        sources.append(ConfigurationSource(name="command line", kind="cli"))

    merged = _deep_merge(base, file_data)
    merged = _deep_merge(merged, env_data)
    merged = _deep_merge(merged, cli_data)
    merged["sources"] = [source.model_dump(mode="json") for source in sources]

    try:
        return Configuration.model_validate(merged)
    except PydanticValidationError as exc:
        raise ConfigurationError(
            "Configuration validation failed.",
            cause=str(exc),
            suggestion="Fix invalid configuration values and retry.",
            documentation="docs/engineering/configuration-system.md",
        ) from exc


def _read_config_file(path: Path) -> dict[str, Any]:
    """Read a YAML or JSON configuration file."""
    if not path.exists():
        raise ConfigurationError(
            "Configuration file does not exist.",
            cause=f"{path} was not found.",
            suggestion="Provide an existing YAML or JSON configuration path.",
            documentation="docs/engineering/configuration-system.md",
        )

    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8")
        if suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(text) or {}
        elif suffix == ".json":
            data = json.loads(text)
        else:
            raise ConfigurationError(
                "Unsupported configuration format.",
                cause=f"{path.suffix} is not supported.",
                suggestion="Use a .yaml, .yml, or .json configuration file.",
                documentation="docs/engineering/configuration-system.md",
            )
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ConfigurationError(
            "Configuration file could not be read.",
            cause=str(exc),
            suggestion="Fix the configuration file and retry.",
            documentation="docs/engineering/configuration-system.md",
        ) from exc

    if not isinstance(data, dict):
        raise ConfigurationError(
            "Configuration file must contain a mapping.",
            cause=f"{path} did not parse to an object.",
            suggestion="Use top-level key-value pairs in configuration files.",
            documentation="docs/engineering/configuration-system.md",
        )
    return data


def _resolve_profile(data: dict[str, Any], selected_profile: str) -> dict[str, Any]:
    """Resolve profile inheritance inside file configuration."""
    profiles = data.get("profiles", {})
    root = {key: value for key, value in data.items() if key != "profiles"}
    if not profiles:
        return root
    if not isinstance(profiles, dict):
        raise ConfigurationError(
            "Profiles must be a mapping.",
            cause="The profiles key did not contain a mapping.",
            suggestion="Define profiles as named configuration mappings.",
            documentation="docs/engineering/configuration-system.md",
        )

    resolved_profile = _resolve_profile_node(profiles, selected_profile, ())
    resolved = _deep_merge(root, resolved_profile)
    resolved["profile"] = selected_profile
    return resolved


def _resolve_profile_node(
    profiles: Mapping[str, Any],
    name: str,
    stack: tuple[str, ...],
) -> dict[str, Any]:
    """Resolve one profile with acyclic inheritance."""
    if name in stack:
        cycle = " -> ".join((*stack, name))
        raise ConfigurationError(
            "Configuration profile inheritance cycle detected.",
            cause=cycle,
            suggestion="Remove cyclic profile inheritance.",
            documentation="docs/engineering/configuration-system.md",
        )
    raw_profile = profiles.get(name)
    if raw_profile is None:
        raise ConfigurationError(
            "Configuration profile does not exist.",
            cause=f"Profile {name!r} was requested but not defined.",
            suggestion="Select an existing profile or define it in the configuration file.",
            documentation="docs/engineering/configuration-system.md",
        )
    if not isinstance(raw_profile, dict):
        raise ConfigurationError(
            "Configuration profile must be a mapping.",
            cause=f"Profile {name!r} is not a mapping.",
            suggestion="Define profile settings as key-value mappings.",
            documentation="docs/engineering/configuration-system.md",
        )

    parent_name = raw_profile.get("extends")
    profile_data = {key: value for key, value in raw_profile.items() if key != "extends"}
    if parent_name is None:
        return profile_data
    if not isinstance(parent_name, str):
        raise ConfigurationError(
            "Configuration profile extends value must be a string.",
            cause=f"Profile {name!r} has non-string extends value.",
            suggestion="Use the name of another profile in extends.",
            documentation="docs/engineering/configuration-system.md",
        )
    parent_data = _resolve_profile_node(profiles, parent_name, (*stack, name))
    return _deep_merge(parent_data, profile_data)


def _env_to_mapping(env: Mapping[str, str]) -> dict[str, Any]:
    """Convert AIHW_BENCH-prefixed environment variables to nested configuration."""
    result: dict[str, Any] = {}
    for key, raw_value in env.items():
        if not key.startswith(ENV_PREFIX):
            continue
        path = [part.lower() for part in key.removeprefix(ENV_PREFIX).split("__") if part]
        if not path:
            continue
        _assign_path(result, path, _parse_env_value(raw_value))
    return result


def _parse_env_value(raw_value: str) -> Any:
    """Parse environment values using YAML scalar/list syntax."""
    try:
        parsed = yaml.safe_load(raw_value)
    except yaml.YAMLError:
        return raw_value
    return raw_value if parsed is None else parsed


def _assign_path(target: dict[str, Any], path: list[str], value: Any) -> None:
    """Assign a nested dictionary value."""
    current = target
    for part in path[:-1]:
        next_value = current.setdefault(part, {})
        if not isinstance(next_value, dict):
            raise ConfigurationError(
                "Environment variable path conflicts with an existing value.",
                cause=f"{part} cannot be both a value and a mapping.",
                suggestion="Use non-conflicting AIHW_BENCH environment variable paths.",
                documentation="docs/engineering/configuration-system.md",
            )
        current = next_value
    current[path[-1]] = value


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Deep merge dictionaries without mutating inputs."""
    merged = deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, Mapping):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None
