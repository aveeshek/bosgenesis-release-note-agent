from fastapi.testclient import TestClient
from starlette.routing import Mount

from grna.mcp.server import create_mcp_app
from grna.mcp.tools import ReleaseNoteMcpTools
from grna.storage.local import LocalArtifactStore, LocalJsonJobStore


def _tools(tmp_path) -> ReleaseNoteMcpTools:
    return ReleaseNoteMcpTools(
        job_store=LocalJsonJobStore(tmp_path / "jobs"),
        artifact_store=LocalArtifactStore(tmp_path / "artifacts"),
    )


def test_scan_start_creates_queued_job(tmp_path) -> None:
    tools = _tools(tmp_path)

    result = tools.github_release_scan_start(
        {
            "repo_url": "https://github.com/aveeshek/bosgenesis-mop-creation-agent",
            "analysis_depth": "standard",
            "output_formats": ["markdown", "html"],
        }
    )

    assert result["job_id"].startswith("scan_")
    assert result["status"] == "queued"

    status = tools.github_release_scan_status({"job_id": result["job_id"]})
    assert status["repo_url"] == "https://github.com/aveeshek/bosgenesis-mop-creation-agent"
    assert status["payload"]["github_repository"]["full_name"] == (
        "aveeshek/bosgenesis-mop-creation-agent"
    )


def test_scan_start_rejects_local_filesystem_path(tmp_path) -> None:
    client = TestClient(create_mcp_app(_tools(tmp_path)))

    response = client.post(
        "/mcp/tools/github_release_scan_start",
        json={"repo_url": "C:/tmp/local-repo"},
    )

    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["error_code"] == "LOCAL_PATH_REJECTED"


def test_artifact_tool_returns_saved_artifacts(tmp_path) -> None:
    tools = _tools(tmp_path)
    job = tools.github_release_scan_start({"repo_url": "https://github.com/example/project"})
    tools.artifact_store.save_artifact(
        job_id=job["job_id"],
        relative_path="release-note.md",
        content=b"# Release",
        artifact_type="markdown",
    )

    result = tools.github_release_get_artifact(
        {"job_id": job["job_id"], "artifact_type": "markdown"}
    )

    assert result["available"] is True
    assert result["artifacts"][0]["artifact_type"] == "markdown"


def test_mcp_http_app_lists_and_invokes_tools(tmp_path) -> None:
    client = TestClient(create_mcp_app(_tools(tmp_path)))

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
    assert payload["result"]["status"] == "queued"


def test_expanded_mcp_contract_tools_are_exposed(tmp_path) -> None:
    tools = _tools(tmp_path)

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


def test_lld_submit_and_cancel_placeholders(tmp_path) -> None:
    tools = _tools(tmp_path)

    submitted = tools.github_release_note_submit_job(
        {
            "repo_url": "https://github.com/example/project",
            "ref": "main",
            "include_pdf": True,
        }
    )
    assert submitted["status"] == "queued"

    status = tools.github_release_note_get_job_status({"job_id": submitted["job_id"]})
    assert status["payload"]["output_formats"] == ["markdown", "html", "pdf"]

    cancelled = tools.github_release_note_cancel_job({"job_id": submitted["job_id"]})
    assert cancelled["cancelled"] is True
    assert cancelled["status"] == "cancelled"


def test_placeholder_summary_and_artifact_aliases(tmp_path) -> None:
    tools = _tools(tmp_path)
    job = tools.scan_github_repository({"repo_url": "https://github.com/example/project"})

    summary = tools.get_repository_analysis_summary({"job_id": job["job_id"]})
    assert summary["available"] is False
    assert summary["summary"] == {}

    artifacts = tools.get_release_note_artifacts({"job_id": job["job_id"]})
    assert artifacts["available"] is False
    assert artifacts["artifacts"] == []


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
