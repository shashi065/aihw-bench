from __future__ import annotations

from pathlib import Path

import pytest

from aihw_bench.domain.errors import SessionError
from aihw_bench.domain.models import BenchmarkSession, SessionStatus
from aihw_bench.infrastructure.storage import FilesystemSessionStore


def test_loading_corrupt_session_file_raises_session_error(tmp_path: Path) -> None:
    store = FilesystemSessionStore(tmp_path)
    session_dir = tmp_path / "corrupt"
    session_dir.mkdir()
    (session_dir / "session.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(SessionError, match="invalid"):
        store.load("corrupt")


def test_loading_missing_session_raises_session_error(tmp_path: Path) -> None:
    store = FilesystemSessionStore(tmp_path)

    with pytest.raises(SessionError, match="does not exist"):
        store.load("missing")


def test_store_artifact_copies_file_and_updates_manifest(tmp_path: Path) -> None:
    store = FilesystemSessionStore(tmp_path)
    session = BenchmarkSession(session_id="artifact-session").finalize(SessionStatus.COMPLETED)
    source = tmp_path / "report.txt"
    source.write_text("artifact payload", encoding="utf-8")

    store.create(session)
    artifact = store.store_artifact("artifact-session", source, kind="report", format="txt")

    assert artifact.sha256 is not None
    assert artifact.path.read_text(encoding="utf-8") == "artifact payload"
    assert "artifact-session" in artifact.source_session_ids


def test_store_artifact_requires_existing_artifact_directory(tmp_path: Path) -> None:
    store = FilesystemSessionStore(tmp_path)
    source = tmp_path / "report.txt"
    source.write_text("artifact payload", encoding="utf-8")

    with pytest.raises(SessionError, match="artifact directory"):
        store.store_artifact("missing-session", source, kind="report", format="txt")
