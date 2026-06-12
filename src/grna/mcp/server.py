"""MCP server and compatibility HTTP tool routes."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from grna.config import get_config

from .schemas import ToolResponse
from .tools import ReleaseNoteMcpTools, error_payload

config = get_config()

mcp = FastMCP(
    "bosgenesis-release-note-agent",
    streamable_http_path="/mcp",
    transport_security=TransportSecuritySettings(allowed_hosts=config.mcp_allowed_hosts),
)


def _invoke(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return ReleaseNoteMcpTools().invoke(tool_name, arguments)


@mcp.tool()
def github_release_scan_start(
    repo_url: str,
    branch: str | None = None,
    tag: str | None = None,
    commit_sha: str | None = None,
    release_name: str | None = None,
    analysis_depth: str = "standard",
    output_formats: list[str] | None = None,
) -> dict[str, Any]:
    """Start a GitHub release-note scan job and return the queued job id."""

    return _invoke(
        "github_release_scan_start",
        {
            "repo_url": repo_url,
            "branch": branch,
            "tag": tag,
            "commit_sha": commit_sha,
            "release_name": release_name,
            "analysis_depth": analysis_depth,
            "output_formats": output_formats or ["markdown", "html"],
        },
    )


@mcp.tool()
def github_release_scan_status(job_id: str) -> dict[str, Any]:
    """Get current status and metadata for a release-note scan job."""

    return _invoke("github_release_scan_status", {"job_id": job_id})


@mcp.tool()
def github_release_get_analytics(job_id: str) -> dict[str, Any]:
    """Get generated analytics JSON for a release-note scan job."""

    return _invoke("github_release_get_analytics", {"job_id": job_id})


@mcp.tool()
def github_release_generate_note(job_id: str) -> dict[str, Any]:
    """Generate or retrieve human-readable release-note artifacts for a job."""

    return _invoke("github_release_generate_note", {"job_id": job_id})


@mcp.tool()
def github_release_get_artifact(
    job_id: str,
    artifact_type: str | None = None,
) -> dict[str, Any]:
    """Get artifact metadata for a release-note job, optionally filtered by type."""

    return _invoke(
        "github_release_get_artifact",
        {"job_id": job_id, "artifact_type": artifact_type},
    )


@mcp.tool()
def github_release_list_evidence(job_id: str) -> dict[str, Any]:
    """List evidence references collected for a release-note scan job."""

    return _invoke("github_release_list_evidence", {"job_id": job_id})


@mcp.tool()
def github_release_get_diagrams(job_id: str) -> dict[str, Any]:
    """Get diagram artifact metadata for a release-note scan job."""

    return _invoke("github_release_get_diagrams", {"job_id": job_id})


@mcp.tool()
def github_release_note_submit_job(
    repo_url: str,
    ref: str | None = None,
    from_ref: str | None = None,
    to_ref: str | None = None,
    include_pdf: bool = True,
    output_profile: str = "enterprise",
    release_name: str | None = None,
    analysis_depth: str = "standard",
) -> dict[str, Any]:
    """Submit a repo scan and release-note generation job."""

    return _invoke(
        "github_release_note_submit_job",
        {
            "repo_url": repo_url,
            "ref": ref,
            "from_ref": from_ref,
            "to_ref": to_ref,
            "include_pdf": include_pdf,
            "output_profile": output_profile,
            "release_name": release_name,
            "analysis_depth": analysis_depth,
        },
    )


@mcp.tool()
def github_release_note_get_job_status(job_id: str) -> dict[str, Any]:
    """Poll current release-note job status."""

    return _invoke("github_release_note_get_job_status", {"job_id": job_id})


@mcp.tool()
def github_release_note_list_artifacts(job_id: str) -> dict[str, Any]:
    """List generated release-note artifacts."""

    return _invoke("github_release_note_list_artifacts", {"job_id": job_id})


@mcp.tool()
def github_release_note_get_artifact(
    job_id: str,
    artifact_type: str | None = None,
    artifact_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve release-note artifact metadata, content reference, or download path."""

    return _invoke(
        "github_release_note_get_artifact",
        {
            "job_id": job_id,
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
        },
    )


@mcp.tool()
def github_release_note_get_evidence(job_id: str) -> dict[str, Any]:
    """Retrieve the structured evidence model for a job."""

    return _invoke("github_release_note_get_evidence", {"job_id": job_id})


@mcp.tool()
def github_release_note_cancel_job(job_id: str) -> dict[str, Any]:
    """Request cancellation for a queued or running release-note job."""

    return _invoke("github_release_note_cancel_job", {"job_id": job_id})


@mcp.tool()
def github_repo_scan_only(
    repo_url: str,
    ref: str | None = None,
    from_ref: str | None = None,
    to_ref: str | None = None,
    analysis_depth: str = "standard",
) -> dict[str, Any]:
    """Submit a repository-understanding scan without release-note generation."""

    return _invoke(
        "github_repo_scan_only",
        {
            "repo_url": repo_url,
            "ref": ref,
            "from_ref": from_ref,
            "to_ref": to_ref,
            "analysis_depth": analysis_depth,
        },
    )


@mcp.tool()
def github_commit_analytics_only(
    repo_url: str,
    ref: str | None = None,
    from_ref: str | None = None,
    to_ref: str | None = None,
    analysis_depth: str = "standard",
) -> dict[str, Any]:
    """Submit a commit analytics only job."""

    return _invoke(
        "github_commit_analytics_only",
        {
            "repo_url": repo_url,
            "ref": ref,
            "from_ref": from_ref,
            "to_ref": to_ref,
            "analysis_depth": analysis_depth,
        },
    )


@mcp.tool()
def github_code_analytics_only(
    repo_url: str,
    ref: str | None = None,
    from_ref: str | None = None,
    to_ref: str | None = None,
    analysis_depth: str = "standard",
) -> dict[str, Any]:
    """Submit a code analytics only job."""

    return _invoke(
        "github_code_analytics_only",
        {
            "repo_url": repo_url,
            "ref": ref,
            "from_ref": from_ref,
            "to_ref": to_ref,
            "analysis_depth": analysis_depth,
        },
    )


@mcp.tool()
def scan_github_repository(
    repo_url: str,
    ref: str | None = None,
    from_ref: str | None = None,
    to_ref: str | None = None,
    include_pdf: bool = True,
    output_profile: str = "enterprise",
) -> dict[str, Any]:
    """Start a GitHub repository scan using the plan-contract tool name."""

    return _invoke(
        "scan_github_repository",
        {
            "repo_url": repo_url,
            "ref": ref,
            "from_ref": from_ref,
            "to_ref": to_ref,
            "include_pdf": include_pdf,
            "output_profile": output_profile,
        },
    )


@mcp.tool()
def get_release_note_job_status(job_id: str) -> dict[str, Any]:
    """Read async release-note job status using the plan-contract tool name."""

    return _invoke("get_release_note_job_status", {"job_id": job_id})


@mcp.tool()
def get_repository_analysis_summary(job_id: str) -> dict[str, Any]:
    """Return the current repository analysis summary for a job."""

    return _invoke("get_repository_analysis_summary", {"job_id": job_id})


@mcp.tool()
def generate_release_note(job_id: str) -> dict[str, Any]:
    """Generate or retrieve release-note artifacts for an existing job."""

    return _invoke("generate_release_note", {"job_id": job_id})


@mcp.tool()
def get_release_note_artifact(
    job_id: str,
    artifact_type: str | None = None,
    artifact_id: str | None = None,
) -> dict[str, Any]:
    """Return release-note artifact metadata or content reference."""

    return _invoke(
        "get_release_note_artifact",
        {
            "job_id": job_id,
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
        },
    )


@mcp.tool()
def get_release_note_artifacts(job_id: str) -> dict[str, Any]:
    """List generated release-note artifacts using the plan-contract tool name."""

    return _invoke("get_release_note_artifacts", {"job_id": job_id})


def streamable_http_app():
    """Return the Streamable HTTP MCP ASGI app for mounting under /mcp."""

    return mcp.streamable_http_app()


def create_mcp_app(tools: ReleaseNoteMcpTools | None = None) -> FastAPI:
    """Create an HTTP app exposing the MCP tool surface."""

    tool_service = tools or ReleaseNoteMcpTools()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(
        title=f"{config.app_name} MCP Server",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health() -> dict[str, str | list[str] | None]:
        return {
            "status": "healthy",
            "service": f"{config.app_name}-mcp",
            "mcp_endpoint": "/mcp",
            "mcp_allowed_hosts": config.mcp_allowed_hosts,
        }

    @app.get("/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready", "service": f"{config.app_name}-mcp"}

    @app.get("/mcp/tools")
    def list_tools() -> dict[str, dict]:
        return {"tools": tool_service.list_tools()}

    @app.post("/mcp/tools/{tool_name}", response_model=ToolResponse)
    def invoke_tool(tool_name: str, arguments: dict) -> ToolResponse:
        try:
            return ToolResponse(ok=True, result=tool_service.invoke(tool_name, arguments))
        except Exception as exc:
            return ToolResponse(ok=False, result={}, error=error_payload(exc))

    app.mount("/", streamable_http_app(), name="mcp")

    return app


def main() -> None:
    """Run the HTTP MCP server with Uvicorn."""

    config = get_config()
    uvicorn.run(
        "grna.mcp.server:create_mcp_app",
        factory=True,
        host=config.mcp_host,
        port=config.mcp_port,
    )


if __name__ == "__main__":
    main()
