"""Hashing helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(content: bytes) -> str:
    """Return SHA-256 hex digest for bytes."""

    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path | str, chunk_size: int = 1024 * 1024) -> str:
    """Return SHA-256 hex digest for a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()

