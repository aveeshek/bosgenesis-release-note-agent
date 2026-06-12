"""Storage data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    """Return a UTC timestamp suitable for JSON records."""

    return datetime.now(tz=UTC).isoformat()


@dataclass(frozen=True, slots=True)
class JobRecord:
    """Minimal persisted scan job status for the local MVP store."""

    job_id: str
    status: str
    stage: str
    created_at: str
    updated_at: str
    repo_url: str | None = None
    progress_percent: int = 0
    error_code: str | None = None
    error_message: str | None = None
    payload: dict[str, Any] | None = None

    @classmethod
    def new(
        cls,
        job_id: str,
        status: str = "queued",
        stage: str = "queued",
        repo_url: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> JobRecord:
        """Create a new job record with timestamps."""

        timestamp = utc_now_iso()
        return cls(
            job_id=job_id,
            status=status,
            stage=stage,
            repo_url=repo_url,
            created_at=timestamp,
            updated_at=timestamp,
            payload=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""

        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> JobRecord:
        """Deserialize from a JSON-compatible dictionary."""

        payload.setdefault("error_code", None)
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class ArtifactMetadata:
    """Metadata for a generated artifact."""

    artifact_id: str
    job_id: str
    artifact_type: str
    path: str
    relative_path: str
    checksum_sha256: str
    size_bytes: int
    created_at: str
    content_type: str | None = None

    @classmethod
    def create(
        cls,
        job_id: str,
        artifact_type: str,
        artifact_path: Path,
        artifact_root: Path,
        checksum_sha256: str,
        size_bytes: int,
        content_type: str | None = None,
    ) -> ArtifactMetadata:
        """Create metadata for an artifact on disk."""

        return cls(
            artifact_id=f"artifact_{uuid4().hex}",
            job_id=job_id,
            artifact_type=artifact_type,
            path=str(artifact_path),
            relative_path=artifact_path.relative_to(artifact_root).as_posix(),
            checksum_sha256=checksum_sha256,
            size_bytes=size_bytes,
            created_at=utc_now_iso(),
            content_type=content_type,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""

        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ArtifactMetadata:
        """Deserialize from a JSON-compatible dictionary."""

        return cls(**payload)
