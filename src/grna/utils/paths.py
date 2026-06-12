"""Root-bound path helpers."""

from __future__ import annotations

from pathlib import Path


class PathTraversalError(ValueError):
    """Raised when a path attempts to escape a configured root directory."""


def resolve_root(root: Path | str) -> Path:
    """Return an absolute root path without requiring it to exist."""

    return Path(root).expanduser().resolve()


def safe_join(root: Path | str, *parts: str | Path) -> Path:
    """Join path parts under root and reject traversal outside root."""

    root_path = resolve_root(root)
    candidate = root_path.joinpath(*parts).resolve()
    if candidate != root_path and root_path not in candidate.parents:
        raise PathTraversalError(f"path escapes configured root: {candidate}")
    return candidate


def ensure_directory(path: Path | str) -> Path:
    """Create a directory if needed and return its resolved path."""

    resolved = resolve_root(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved

