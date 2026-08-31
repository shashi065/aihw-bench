import logging

import pytest

from aihw_bench.domain.errors import SecurityError
from aihw_bench.utils.hashing import sha256_file
from aihw_bench.utils.logging import configure_logging, redact_secrets
from aihw_bench.utils.paths import resolve_within
from aihw_bench.utils.time import monotonic_seconds, utc_now


def test_resolve_within_rejects_path_traversal(tmp_path) -> None:
    with pytest.raises(SecurityError):
        resolve_within(tmp_path, tmp_path / ".." / "outside.txt")


def test_sha256_file_returns_digest(tmp_path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("aihw-bench\n", encoding="utf-8")

    assert (
        sha256_file(artifact) == "1fefa58e89bfe9c5f00977e1b1a673ee025b5290cbfe27c1631d61a2a693f6bd"
    )


def test_sha256_file_rejects_non_positive_chunk_size(tmp_path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("aihw-bench\n", encoding="utf-8")

    with pytest.raises(ValueError, match="positive"):
        sha256_file(artifact, chunk_size=0)


def test_redact_secrets_masks_common_assignments() -> None:
    message = "token=abc password=hunter2 api_key=secret"

    assert redact_secrets(message) == "token=<redacted> password=<redacted> api_key=<redacted>"


def test_configure_logging_installs_redaction_filter(capsys) -> None:
    logger = configure_logging(level=logging.INFO, logger_name="aihw_bench.test")

    logger.info("secret=value")

    assert "secret=<redacted>" in capsys.readouterr().err


def test_clocks_return_valid_values() -> None:
    assert utc_now().tzinfo is not None
    assert monotonic_seconds() > 0
