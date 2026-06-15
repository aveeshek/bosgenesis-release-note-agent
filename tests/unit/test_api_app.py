from fastapi.testclient import TestClient

from grna.api.app import create_app
from grna.mcp.tools import ReleaseNoteMcpTools
from grna.storage.local import LocalArtifactStore, LocalJsonJobStore
from grna.storage.models import JobRecord


def _client(tmp_path, monkeypatch=None) -> tuple[TestClient, ReleaseNoteMcpTools]:
    tools = ReleaseNoteMcpTools(
        job_store=LocalJsonJobStore(tmp_path / "jobs"),
        artifact_store=LocalArtifactStore(tmp_path / "artifacts"),
    )
    if monkeypatch is not None:
        monkeypatch.setattr(
            "grna.mcp.tools.run_end_to_end_scan",
            lambda request, **kwargs: _fake_scan(request, **kwargs),
        )
    return TestClient(create_app(tools)), tools


def _fake_scan(request, *, job_store, artifact_store, **_) -> dict:
    job = job_store.save(
        JobRecord.new(
            job_id="scan_api",
            status="completed",
            stage="completed",
            repo_url=request.repo_url,
            payload={
                "repo_url": request.repo_url,
                "output_formats": list(request.output_formats),
                **(request.payload_extra or {}),
            },
        )
    )
    artifact_store.save_artifact(
        job.job_id,
        "analytics.json",
        b'{"job_id":"scan_api","sections":{},"gaps":[],"warnings":[],"evidence_ids":[]}',
        "analytics",
        "application/json",
    )
    markdown = artifact_store.save_artifact(
        job.job_id,
        "release-note.md",
        b"# Release\n",
        "markdown",
        "text/markdown",
    )
    return {
        "job_id": job.job_id,
        "status": job.status,
        "stage": job.stage,
        "progress_percent": 100,
        "repository": request.repo_url,
        "resolved_commit_sha": "abc123",
        "artifacts": [
            artifact.to_dict()
            for artifact in artifact_store.list_artifacts(job.job_id)
        ],
        "markdown_artifact_id": markdown.artifact_id,
    }


def test_api_health_and_readiness_endpoints(tmp_path) -> None:
    client, _ = _client(tmp_path)

    health = client.get("/health")
    ready = client.get("/ready")

    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_api_scan_creation_and_status_query(tmp_path, monkeypatch) -> None:
    client, _ = _client(tmp_path, monkeypatch)

    created = client.post(
        "/api/v1/scans",
        json={
            "repo_url": "https://github.com/aveeshek/bosgenesis-mop-creation-agent",
            "analysis_depth": "standard",
            "output_formats": ["markdown", "html"],
        },
    )

    assert created.status_code == 202
    payload = created.json()
    assert payload["job_id"].startswith("scan_")
    assert payload["status"] == "completed"
    assert payload["artifacts"]

    status = client.get(f"/api/v1/scans/{payload['job_id']}")
    assert status.status_code == 200
    status_payload = status.json()
    assert status_payload["repo_url"] == (
        "https://github.com/aveeshek/bosgenesis-mop-creation-agent"
    )
    assert status_payload["payload"]["github_repository"]["full_name"] == (
        "aveeshek/bosgenesis-mop-creation-agent"
    )


def test_api_rejects_invalid_scan_url(tmp_path) -> None:
    client, _ = _client(tmp_path)

    response = client.post("/api/v1/scans", json={"repo_url": "C:/tmp/local-repo"})

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "LOCAL_PATH_REJECTED"


def test_api_analytics_endpoint_returns_generated_contract(tmp_path, monkeypatch) -> None:
    client, _ = _client(tmp_path, monkeypatch)
    created = client.post(
        "/api/v1/scans",
        json={"repo_url": "https://github.com/example/project"},
    ).json()

    response = client.get(f"/api/v1/scans/{created['job_id']}/analytics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == created["job_id"]
    assert payload["available"] is True
    assert payload["analytics"]["job_id"] == created["job_id"]


def test_api_artifact_listing_metadata_and_download(tmp_path, monkeypatch) -> None:
    client, _ = _client(tmp_path, monkeypatch)
    created = client.post(
        "/api/v1/scans",
        json={"repo_url": "https://github.com/example/project"},
    ).json()
    artifact = next(
        artifact for artifact in created["artifacts"] if artifact["artifact_type"] == "markdown"
    )

    listed = client.get(
        f"/api/v1/scans/{created['job_id']}/artifacts",
        params={"artifact_type": "markdown"},
    )
    assert listed.status_code == 200
    listed_payload = listed.json()
    assert listed_payload["available"] is True
    assert listed_payload["artifacts"][0]["artifact_id"] == artifact["artifact_id"]

    metadata = client.get(
        f"/api/v1/scans/{created['job_id']}/artifacts/{artifact['artifact_id']}"
    )
    assert metadata.status_code == 200
    assert metadata.json()["artifacts"][0]["checksum_sha256"] == artifact["checksum_sha256"]

    download = client.get(
        f"/api/v1/scans/{created['job_id']}/artifacts/{artifact['artifact_id']}/download"
    )
    assert download.status_code == 200
    assert download.content == b"# Release\n"
    assert download.headers["content-type"].startswith("text/markdown")


def test_api_missing_job_returns_404(tmp_path) -> None:
    client, _ = _client(tmp_path)

    response = client.get("/api/v1/scans/scan_missing")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "JOB_NOT_FOUND"
