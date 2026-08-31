"""Serialization helpers for domain models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


def to_jsonable(value: BaseModel | dict[str, Any] | list[Any]) -> Any:
    """Convert a supported value to a JSON-serializable object."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value


def write_json(path: Path, value: BaseModel | dict[str, Any] | list[Any]) -> None:
    """Write a JSON file with deterministic formatting."""
    path.write_text(
        json.dumps(to_jsonable(value), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from a file."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return value


def write_yaml(path: Path, value: BaseModel | dict[str, Any]) -> None:
    """Write a YAML file with deterministic key ordering."""
    path.write_text(yaml.safe_dump(to_jsonable(value), sort_keys=True), encoding="utf-8")
