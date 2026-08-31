from datetime import UTC, datetime

import pytest

from aihw_bench.domain.errors import SecurityError, SessionError
from aihw_bench.domain.models import BenchmarkSession, SessionStatus
from aihw_bench.infrastructure.storage import FilesystemSessionStore
from aihw_bench.infrastructure.storage.filesystem import MAX_ARTIFACT_BYTES


def test_filesystem_session_store_creates_and_loads_session(tmp_path) -> None:
    store = FilesystemSessionStore(tmp_path)
    session = BenchmarkSession(session_id="session-1").finalize(SessionStatus.COMPLETED)

    session_path = store.create(session)
    loaded = store.load("session-1")

    assert session_path.name == "session-1"
    assert loaded.session_id == "session-1"
    assert loaded.status is SessionStatus.COMPLETED
    assert (session_path / "session.json").exists()
    assert (session_path / "config.resolved.yaml").exists()
    assert (session_path / "manifest.json").exists()


def test_filesystem_session_store_rejects_duplicate_session(tmp_path) -> None:
    store = FilesystemSessionStore(tmp_path)
    session = BenchmarkSession(session_id="session-1").finalize(SessionStatus.COMPLETED)

    store.create(session)

    with pytest.raises(SessionError, match="already exists"):
        store.create(session)


def test_filesystem_session_store_rejects_path_traversal(tmp_path) -> None:
    store = FilesystemSessionStore(tmp_path)

    with pytest.raises(SecurityError):
        store.session_path("../outside")


def test_filesystem_session_store_lists_sessions(tmp_path) -> None:
    store = FilesystemSessionStore(tmp_path)
    first = BenchmarkSession(session_id="a").finalize(SessionStatus.COMPLETED)
    second = BenchmarkSession(
        session_id="b",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    ).finalize(SessionStatus.FAILED)

    store.create(second)
    store.create(first)

    assert store.list_sessions() == ["a", "b"]


def test_filesystem_session_store_streams_artifact_and_updates_manifest(tmp_path) -> None:
    store = FilesystemSessionStore(tmp_path / "sessions")
    store.create(BenchmarkSession(session_id="artifact").finalize(SessionStatus.COMPLETED))
    source = tmp_path / "result.bin"
    source.write_bytes(b"artifact-data" * 2048)

    artifact = store.store_artifact("artifact", source, kind="report", format="bin")

    assert artifact.path.read_bytes() == source.read_bytes()
    assert artifact.sha256
    assert not (artifact.path.parent / ".result.bin.partial").exists()


def test_filesystem_session_store_rejects_missing_or_oversized_artifact(
    tmp_path, monkeypatch
) -> None:
    store = FilesystemSessionStore(tmp_path / "sessions")
    store.create(BenchmarkSession(session_id="artifact").finalize(SessionStatus.COMPLETED))

    with pytest.raises(SessionError, match="does not exist"):
        store.store_artifact("artifact", tmp_path / "missing.bin", kind="report", format="bin")

    source = tmp_path / "too-large.bin"
    source.write_bytes(b"x")
    monkeypatch.setattr("aihw_bench.infrastructure.storage.filesystem.MAX_ARTIFACT_BYTES", 0)
    with pytest.raises(SessionError, match="size limit"):
        store.store_artifact("artifact", source, kind="report", format="bin")

    assert MAX_ARTIFACT_BYTES > 0
