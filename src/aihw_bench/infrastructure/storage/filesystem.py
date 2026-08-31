"""Filesystem-backed immutable session store."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from pydantic import ValidationError as PydanticValidationError

from aihw_bench.domain.errors import SessionError
from aihw_bench.domain.models import BenchmarkSession, ExportArtifact
from aihw_bench.utils.hashing import sha256_file
from aihw_bench.utils.paths import ensure_directory, resolve_within
from aihw_bench.utils.serialization import read_json, write_json, write_yaml

MAX_ARTIFACT_BYTES = 512 * 1024 * 1024
COPY_CHUNK_BYTES = 1024 * 1024


class FilesystemSessionStore:
    """Store immutable benchmark sessions on the local filesystem."""

    def __init__(self, root: Path) -> None:
        self.root = ensure_directory(root)

    def session_path(self, session_id: str) -> Path:
        """Return the resolved path for a session ID."""
        return resolve_within(self.root, self.root / session_id)

    def create(self, session: BenchmarkSession) -> Path:
        """Persist a new immutable session and return its directory."""
        path = self.session_path(session.session_id)
        if path.exists():
            raise SessionError(
                "Session already exists.",
                cause=f"{path} already exists.",
                suggestion="Use a unique session ID or load the existing session.",
                documentation="docs/engineering/storage-design.md",
            )

        path.mkdir(parents=True)
        artifacts_dir = path / "artifacts"
        artifacts_dir.mkdir()
        write_json(path / "session.json", session)
        write_yaml(path / "config.resolved.yaml", session.configuration)
        write_json(
            path / "metrics.json", [metric.model_dump(mode="json") for metric in session.metrics]
        )
        write_json(path / "system.json", session.system)
        write_json(path / "manifest.json", self._manifest(session))
        return path

    def load(self, session_id: str) -> BenchmarkSession:
        """Load a session by ID."""
        path = self.session_path(session_id)
        session_file = path / "session.json"
        if not session_file.exists():
            raise SessionError(
                "Session does not exist.",
                cause=f"{session_file} was not found.",
                suggestion="Check the session ID and storage root.",
                documentation="docs/engineering/storage-design.md",
            )
        try:
            return BenchmarkSession.model_validate(read_json(session_file))
        except (ValueError, PydanticValidationError) as exc:
            raise SessionError(
                "Session data is invalid.",
                cause=str(exc),
                suggestion="Inspect the session schema version and file contents.",
                documentation="docs/engineering/storage-design.md",
            ) from exc

    def list_sessions(self) -> list[str]:
        """Return session IDs stored under the root directory."""
        return sorted(
            child.name
            for child in self.root.iterdir()
            if child.is_dir() and (child / "session.json").exists()
        )

    def store_artifact(
        self, session_id: str, source: Path, *, kind: str, format: str
    ) -> ExportArtifact:
        """Copy an artifact into a session's artifact directory."""
        session_dir = self.session_path(session_id)
        artifacts_dir = resolve_within(session_dir, session_dir / "artifacts")
        if not artifacts_dir.exists():
            raise SessionError(
                "Session artifact directory does not exist.",
                cause=f"{artifacts_dir} was not found.",
                suggestion="Create the session before storing artifacts.",
                documentation="docs/engineering/storage-design.md",
            )
        if not source.is_file():
            raise SessionError(
                "Artifact source does not exist or is not a file.",
                cause=f"{source} is not a readable regular file.",
                suggestion="Provide an existing artifact file.",
                documentation="docs/engineering/storage-design.md",
            )
        source_size = source.stat().st_size
        if source_size > MAX_ARTIFACT_BYTES:
            raise SessionError(
                "Artifact exceeds the local storage size limit.",
                cause=f"Artifact size {source_size} exceeds {MAX_ARTIFACT_BYTES} bytes.",
                suggestion=(
                    "Store a smaller artifact or publish it through an external artifact service."
                ),
                documentation="docs/engineering/storage-design.md",
            )
        destination = resolve_within(artifacts_dir, artifacts_dir / source.name)
        temporary = resolve_within(artifacts_dir, artifacts_dir / f".{source.name}.partial")
        try:
            with source.open("rb") as input_file, temporary.open("xb") as output_file:
                shutil.copyfileobj(input_file, output_file, length=COPY_CHUNK_BYTES)
                output_file.flush()
                os.fsync(output_file.fileno())
            temporary.replace(destination)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise SessionError(
                "Artifact copy failed.",
                cause=str(exc),
                suggestion="Check disk space and artifact permissions before retrying.",
                documentation="docs/engineering/storage-design.md",
            ) from exc
        artifact = ExportArtifact(
            artifact_id=source.stem,
            kind=kind,
            format=format,
            path=destination,
            sha256=sha256_file(destination),
            source_session_ids=[session_id],
        )
        write_json(session_dir / "manifest.json", self._manifest(self.load(session_id), [artifact]))
        return artifact

    @staticmethod
    def _manifest(
        session: BenchmarkSession,
        extra_artifacts: list[ExportArtifact] | None = None,
    ) -> dict[str, object]:
        artifacts = [*session.artifacts, *(extra_artifacts or [])]
        return {
            "session_id": session.session_id,
            "schema_version": session.schema_version,
            "artifacts": [artifact.model_dump(mode="json") for artifact in artifacts],
        }
