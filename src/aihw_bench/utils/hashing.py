"""Hashing helpers for artifact integrity."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest for a file.

    Args:
        path: File to hash.
        chunk_size: Number of bytes read per chunk.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")

    digest = sha256()
    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
