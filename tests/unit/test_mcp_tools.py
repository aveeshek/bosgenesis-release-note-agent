from time import monotonic, sleep

from fastapi.testclient import TestClient
from starlette.routing import Mount

from grna.mcp.server import create_mcp_app
from grna.mcp.tools import ReleaseNoteMcpTools
from grna.storage.local import LocalArtifactStore, LocalJsonJobStore
from grna.storage.models import JobRecord


def _tools(tmp_path, monkeypatch=None) -> ReleaseNoteMcpTools:
    tools = ReleaseNoteMcpTools(
        job_store=LocalJsonJobStore(tmp_path / "jobs"),
        artifact_store=LocalArtifactStore(tmp_path / "artifacts"),
    )
    if monkeypatch is not None:
        monkeypatch.setattr(
            "grna.mcp.tools.run_end_to_end_scan",
            lambda request, **kwargs: _fake_scan(request, **kwargs),
        )
    return tools


def _fake_scan(request, *, job_store, artifact_store, **_) -> dict:
    job_id = request.job_id or "scan_test"
    job = JobRecord.new(
        job_id=job_id,
        status="completed",
        stage="completed",
        repo_url=request.repo_url,
        payload={
            "repo_url": request.repo_url,
            "output_formats": list(request.output_formats),
            **(request.payload_extra or {}),
        },
    )
    job = job_store.save(job)
    artifact_store.save_artifact(
        job.job_id,
        "analytics.json",
        (
            '{"job_id":"'
            + job_id
            + '","sections":{},"gaps":[],"warnings":[],"evidence_ids":[]}'
        ).encode("utf-8"),
        "analytics",
        "application/json",
    )
    artifact_store.save_artifact(
        job.job_id,
        "evidence.json",
        b'{"records":[]}',
        "evidence",
        "application/json",
    )
    markdown = artifact_store.save_artifact(
        job.job_id,
        "release-note.md",
        b"# Release",
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


def _plain_tools(tmp_path) -> ReleaseNoteMcpTools:
    return ReleaseNoteMcpTools(
        job_store=LocalJsonJobStore(tmp_path / "jobs"),
        artifact_store=LocalArtifactStore(tmp_path / "artifacts"),
    )


def test_scan_start_runs_end_to_end_job(tmp_path, monkeypatch) -> None:
    tools = _tools(tmp_path, monkeypatch)

    result = tools.github_release_scan_start(
        {
            "repo_url": "https://github.com/aveeshek/bosgenesis-mop-creation-agent",
            "analysis_depth": "standard",
            "output_formats": ["markdown", "html"],
        }
    )

    assert result["job_id"].startswith("scan_")
    assert result["status"] == "completed"
    assert result["artifacts"]

    status = tools.github_release_scan_status({"job_id": result["job_id"]})
    assert status["repo_url"] == "https://github.com/aveeshek/bosgenesis-mop-creation-agent"
    assert status["payload"]["github_repository"]["full_name"] == (
        "aveeshek/bosgenesis-mop-creation-agent"
    )


def test_scan_start_rejects_local_filesystem_path(tmp_path) -> None:
    client = TestClient(create_mcp_app(_plain_tools(tmp_path)))

    response = client.post(
        "/mcp/tools/github_release_scan_start",
        json={"repo_url": "C:/tmp/local-repo"},
    )

    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["error_code"] == "LOCAL_PATH_REJECTED"


def test_artifact_tool_returns_saved_artifacts(tmp_path) -> None:
    tools = _tools(tmp_path, monkeypatch=None)
    # Submit through the local store directly so this test focuses on artifact lookup.
    tools.job_store.save(
        JobRecord.new(
            job_id="scan_artifact",
            status="completed",
            stage="completed",
            repo_url="https://github.com/example/project",
        )
    )
    tools.artifact_store.save_artifact(
        job_id="scan_artifact",
        relative_path="release-note.md",
        content=b"# Release",
        artifact_type="markdown",
    )

    result = tools.github_release_get_artifact(
        {"job_id": "scan_artifact", "artifact_type": "markdown"}
    )

    assert result["available"] is True
    assert result["artifacts"][0]["artifact_type"] == "markdown"


def test_mcp_http_app_lists_and_invokes_tools(tmp_path, monkeypatch) -> None:
    client = TestClient(create_mcp_app(_tools(tmp_path, monkeypatch)))

    tools_response = client.get("/mcp/tools")
    assert tools_response.status_code == 200
    tool_names = tools_response.json()["tools"]
    assert "github_release_scan_start" in tool_names
    assert "github_release_note_submit_job" in tool_names
    assert "scan_github_repository" in tool_names

    invoke_response = client.post(
        "/mcp/tools/github_release_scan_start",
        json={"repo_url": "https://github.com/example/project"},
    )

    payload = invoke_response.json()
    assert payload["ok"] is True
    assert payload["result"]["status"] == "completed"


def test_expanded_mcp_contract_tools_are_exposed(tmp_path) -> None:
    tools = _plain_tools(tmp_path)

    expected_tools = {
        "github_release_scan_start",
        "github_release_scan_status",
        "github_release_get_analytics",
        "github_release_generate_note",
        "github_release_get_artifact",
        "github_release_list_evidence",
        "github_release_get_diagrams",
        "github_release_note_submit_job",
        "github_release_note_get_job_status",
        "github_release_note_list_artifacts",
        "github_release_note_get_artifact",
        "github_release_note_get_evidence",
        "github_release_note_cancel_job",
        "github_repo_scan_only",
        "github_commit_analytics_only",
        "github_code_analytics_only",
        "scan_github_repository",
        "get_release_note_job_status",
        "get_repository_analysis_summary",
        "generate_release_note",
        "get_release_note_artifact",
        "get_release_note_artifacts",
    }

    assert expected_tools.issubset(tools.list_tools())


def test_lld_submit_runs_end_to_end(tmp_path, monkeypatch) -> None:
    tools = _tools(tmp_path, monkeypatch)

    submitted = tools.github_release_note_submit_job(
        {
            "repo_url": "https://github.com/example/project",
            "ref": "main",
            "include_pdf": True,
        }
    )
    assert submitted["accepted"] is True
    assert submitted["async"] is True
    assert submitted["status"] == "queued"
    assert submitted["artifacts"] == []

    status = _wait_for_status(tools, submitted["job_id"], "completed")
    assert status["payload"]["output_formats"] == ["markdown", "html", "pdf"]


def test_summary_and_artifact_aliases(tmp_path, monkeypatch) -> None:
    tools = _tools(tmp_path, monkeypatch)
    job = tools.scan_github_repository({"repo_url": "https://github.com/example/project"})
    _wait_for_status(tools, job["job_id"], "completed")

    summary = tools.get_repository_analysis_summary({"job_id": job["job_id"]})
    assert summary["available"] is True
    assert summary["summary"]["evidence_count"] == 0

    artifacts = tools.get_release_note_artifacts({"job_id": job["job_id"]})
    assert artifacts["available"] is True
    assert artifacts["artifacts"]


def _wait_for_status(tools: ReleaseNoteMcpTools, job_id: str, status: str) -> dict:
    deadline = monotonic() + 5
    last = {}
    while monotonic() < deadline:
        last = tools.github_release_scan_status({"job_id": job_id})
        if last["status"] == status:
            return last
        sleep(0.05)
    raise AssertionError(f"Job {job_id} did not reach {status}; last status: {last}")


def test_streamable_http_mcp_mount_exists(tmp_path) -> None:
    app = create_mcp_app(_tools(tmp_path))

    assert any(isinstance(route, Mount) and route.path == "" for route in app.routes)

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["mcp_endpoint"] == "/mcp"


def test_unknown_tool_returns_structured_error(tmp_path) -> None:
    client = TestClient(create_mcp_app(_tools(tmp_path)))

    response = client.post("/mcp/tools/not_real", json={})

    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["error_code"] == "UNKNOWN_TOOL"
