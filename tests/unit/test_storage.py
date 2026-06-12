import json

import pytest

from grna.storage.local import LocalArtifactStore, LocalJsonJobStore
from grna.storage.models import JobRecord
from grna.utils.hashing import sha256_bytes
from grna.utils.paths import PathTraversalError, safe_join


def test_safe_join_rejects_parent_traversal(tmp_path) -> None:
    with pytest.raises(PathTraversalError):
        safe_join(tmp_path, "..", "escape.txt")


def test_safe_join_allows_nested_paths(tmp_path) -> None:
    nested = safe_join(tmp_path, "job_001", "release-note.md")

    assert nested == tmp_path.resolve() / "job_001" / "release-note.md"


def test_local_json_job_store_saves_and_loads_job_status(tmp_path) -> None:
    store = LocalJsonJobStore(tmp_path / "jobs")
    job = JobRecord.new(
        job_id="job_001",
        repo_url="https://github.com/example/project",
        payload={"analysis_depth": "standard"},
    )

    store.save(job)
    loaded = store.get("job_001")

    assert loaded == job
    assert (tmp_path / "jobs" / "job_001.json").exists()


def test_local_json_job_store_rejects_traversal_job_id(tmp_path) -> None:
    store = LocalJsonJobStore(tmp_path / "jobs")

    with pytest.raises(PathTraversalError):
        store.get("../escape")


def test_artifact_store_writes_artifact_metadata_and_manifest(tmp_path) -> None:
    store = LocalArtifactStore(tmp_path / "artifacts")
    content = b"# Release Note\n"

    metadata = store.save_artifact(
        job_id="job_001",
        relative_path="release-note.md",
        content=content,
        artifact_type="markdown",
        content_type="text/markdown",
    )

    assert metadata.job_id == "job_001"
    assert metadata.artifact_type == "markdown"
    assert metadata.checksum_sha256 == sha256_bytes(content)
    assert metadata.size_bytes == len(content)
    assert metadata.created_at
    assert metadata.path.endswith("release-note.md")
    assert metadata.relative_path.endswith("job_001/release-note.md")

    manifest_path = tmp_path / "artifacts" / "job_001" / "artifacts.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["artifacts"][0]["artifact_id"] == metadata.artifact_id


def test_artifact_store_rejects_relative_path_escape(tmp_path) -> None:
    store = LocalArtifactStore(tmp_path / "artifacts")

    with pytest.raises(PathTraversalError):
        store.save_artifact(
            job_id="job_001",
            relative_path="../release-note.md",
            content=b"unsafe",
            artifact_type="markdown",
        )


def test_artifact_store_lists_artifact_metadata(tmp_path) -> None:
    store = LocalArtifactStore(tmp_path / "artifacts")
    saved = store.save_artifact(
        job_id="job_001",
        relative_path="diagrams/runtime-flow.mmd",
        content=b"flowchart LR",
        artifact_type="diagram",
    )

    artifacts = store.list_artifacts("job_001")

    assert artifacts == [saved]

