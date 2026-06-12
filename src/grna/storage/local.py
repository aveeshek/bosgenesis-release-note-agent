"""Local JSON and filesystem storage implementation."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from grna.storage.models import ArtifactMetadata, JobRecord
from grna.utils.hashing import sha256_file
from grna.utils.paths import ensure_directory, safe_join


class JobNotFoundError(KeyError):
    """Raised when a job record is not found."""


class LocalJsonJobStore:
    """Persist scan job records as `data/jobs/{job_id}.json` files."""

    def __init__(self, job_root: Path | str = "data/jobs") -> None:
        self.job_root = ensure_directory(job_root)

    def _job_path(self, job_id: str) -> Path:
        return safe_join(self.job_root, f"{job_id}.json")

    def save(self, job: JobRecord) -> JobRecord:
        """Write a job record atomically enough for local MVP usage."""

        destination = self._job_path(job.job_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(job.to_dict(), indent=2, sort_keys=True)
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=destination.parent,
            delete=False,
        ) as temp_file:
            temp_file.write(payload)
            temp_path = Path(temp_file.name)
        temp_path.replace(destination)
        return job

    def get(self, job_id: str) -> JobRecord:
        """Load a job record by ID."""

        path = self._job_path(job_id)
        if not path.exists():
            raise JobNotFoundError(job_id)
        with path.open("r", encoding="utf-8") as file_handle:
            return JobRecord.from_dict(json.load(file_handle))


class LocalArtifactStore:
    """Persist generated artifacts under `data/artifacts/{job_id}`."""

    MANIFEST_NAME = "artifacts.json"

    def __init__(self, artifact_root: Path | str = "data/artifacts") -> None:
        self.artifact_root = ensure_directory(artifact_root)

    def job_artifact_dir(self, job_id: str) -> Path:
        """Return a safe artifact directory for a job."""

        return safe_join(self.artifact_root, job_id)

    def _manifest_path(self, job_id: str) -> Path:
        return safe_join(self.job_artifact_dir(job_id), self.MANIFEST_NAME)

    def _artifact_path(self, job_id: str, relative_path: str) -> Path:
        return safe_join(self.job_artifact_dir(job_id), relative_path)

    def save_artifact(
        self,
        job_id: str,
        relative_path: str,
        content: bytes,
        artifact_type: str,
        content_type: str | None = None,
    ) -> ArtifactMetadata:
        """Write artifact content and update the job artifact manifest."""

        artifact_path = self._artifact_path(job_id, relative_path)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(content)

        metadata = ArtifactMetadata.create(
            job_id=job_id,
            artifact_type=artifact_type,
            artifact_path=artifact_path,
            artifact_root=self.artifact_root,
            checksum_sha256=sha256_file(artifact_path),
            size_bytes=artifact_path.stat().st_size,
            content_type=content_type,
        )
        self._append_manifest(job_id, metadata)
        return metadata

    def list_artifacts(self, job_id: str) -> list[ArtifactMetadata]:
        """Return artifact metadata for a job."""

        manifest_path = self._manifest_path(job_id)
        if not manifest_path.exists():
            return []
        with manifest_path.open("r", encoding="utf-8") as file_handle:
            payload = json.load(file_handle)
        return [ArtifactMetadata.from_dict(item) for item in payload.get("artifacts", [])]

    def _append_manifest(self, job_id: str, metadata: ArtifactMetadata) -> None:
        manifest_path = self._manifest_path(job_id)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        existing = [item.to_dict() for item in self.list_artifacts(job_id)]
        existing.append(metadata.to_dict())
        manifest_path.write_text(
            json.dumps({"artifacts": existing}, indent=2, sort_keys=True),
            encoding="utf-8",
        )

