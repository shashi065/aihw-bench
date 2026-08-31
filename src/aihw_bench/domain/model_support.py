"""Protocols and request/result models for model loading."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from aihw_bench.domain.models import ModelMetadata, WorkloadConfig


@dataclass(frozen=True, slots=True)
class ModelLoadRequest:
    """Request describing a model source to be loaded."""

    source: Path
    framework: str | None = None
    name: str | None = None
    precision: str | None = None
    input_shapes: Mapping[str, Sequence[int]] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LoadedModel:
    """Resolved model handle and extracted metadata."""

    source: Path
    loader_name: str
    metadata: ModelMetadata
    handle: Any | None = None


@runtime_checkable
class ModelLoader(Protocol):
    """Contract implemented by format-specific model loaders."""

    name: str
    supported_extensions: frozenset[str]

    def can_load(self, source: Path) -> bool:
        """Return whether the loader can handle the given file path."""

    def load(self, request: ModelLoadRequest) -> LoadedModel:
        """Load a model file and return metadata plus the resolved handle."""


@runtime_checkable
class ModelLoaderCatalog(Protocol):
    """Registry interface used by application services."""

    def load(self, request: ModelLoadRequest) -> LoadedModel:
        """Load a model from an explicit load request."""

    def load_workload(self, workload: WorkloadConfig) -> LoadedModel:
        """Load a model from resolved configuration."""
