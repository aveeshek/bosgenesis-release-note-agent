"""FastAPI application factory for the REST API runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError

from grna.config import get_config
from grna.mcp.schemas import AnalysisDepth, OutputFormat
from grna.mcp.tools import ReleaseNoteMcpTools, error_payload
from grna.observability import record_artifact_download_audit
from grna.storage.models import ArtifactMetadata


class ScanCreateRequest(BaseModel):
    """REST request body for starting a scan job."""

    repo_url: str
    branch: str | None = None
    tag: str | None = None
    commit_sha: str | None = None
    release_name: str | None = None
    analysis_depth: AnalysisDepth = "standard"
    output_formats: list[OutputFormat] = Field(default_factory=lambda: ["markdown", "html"])


def create_app(tools: ReleaseNoteMcpTools | None = None) -> FastAPI:
    """Create the REST API app."""

    config = get_config()
    app = FastAPI(title=config.app_name, version="0.1.0")
    app.state.release_note_tools = tools or ReleaseNoteMcpTools()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy", "service": config.app_name}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready", "service": config.app_name}

    @app.post("/api/v1/scans", status_code=202)
    def create_scan(request: ScanCreateRequest) -> dict[str, Any]:
        return _invoke_tool(
            app,
            "github_release_scan_start",
            request.model_dump(mode="json"),
        )

    @app.get("/api/v1/scans/{job_id}")
    def get_scan(job_id: str) -> dict[str, Any]:
        return _invoke_tool(app, "github_release_scan_status", {"job_id": job_id})

    @app.get("/api/v1/scans/{job_id}/analytics")
    def get_analytics(job_id: str) -> dict[str, Any]:
        return _invoke_tool(app, "github_release_get_analytics", {"job_id": job_id})

    @app.get("/api/v1/scans/{job_id}/artifacts")
    def list_artifacts(job_id: str, artifact_type: str | None = None) -> dict[str, Any]:
        return _invoke_tool(
            app,
            "github_release_get_artifact",
            {"job_id": job_id, "artifact_type": artifact_type},
        )

    @app.get("/api/v1/scans/{job_id}/artifacts/{artifact_id}")
    def get_artifact(job_id: str, artifact_id: str) -> dict[str, Any]:
        return _invoke_tool(
            app,
            "github_release_note_get_artifact",
            {"job_id": job_id, "artifact_id": artifact_id},
        )

    @app.get("/api/v1/scans/{job_id}/artifacts/{artifact_id}/download")
    def download_artifact(job_id: str, artifact_id: str) -> FileResponse:
        artifact = _get_artifact_metadata(app, job_id, artifact_id)
        artifact_path = _safe_artifact_path(app, job_id, artifact)
        if not artifact_path.exists() or not artifact_path.is_file():
            record_artifact_download_audit(
                job_id=job_id,
                artifact_id=artifact_id,
                artifact_type=artifact.artifact_type,
                relative_path=artifact.relative_path,
                status="missing",
            )
            raise HTTPException(status_code=404, detail="Artifact file not found.")
        record_artifact_download_audit(
            job_id=job_id,
            artifact_id=artifact_id,
            artifact_type=artifact.artifact_type,
            relative_path=artifact.relative_path,
            status="ok",
        )
        return FileResponse(
            artifact_path,
            media_type=artifact.content_type or "application/octet-stream",
            filename=Path(artifact.relative_path).name,
        )

    return app


def _tools(app: FastAPI) -> ReleaseNoteMcpTools:
    return app.state.release_note_tools


def _invoke_tool(app: FastAPI, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        return _tools(app).invoke(tool_name, arguments)
    except Exception as exc:
        _raise_http_error(exc)


def _get_artifact_metadata(app: FastAPI, job_id: str, artifact_id: str) -> ArtifactMetadata:
    _invoke_tool(app, "github_release_scan_status", {"job_id": job_id})
    for artifact in _tools(app).artifact_store.list_artifacts(job_id):
        if artifact.artifact_id == artifact_id:
            return artifact
    raise HTTPException(status_code=404, detail="Artifact not found.")


def _safe_artifact_path(
    app: FastAPI,
    job_id: str,
    artifact: ArtifactMetadata,
) -> Path:
    artifact_root = _tools(app).artifact_store.job_artifact_dir(job_id).resolve()
    artifact_path = Path(artifact.path).resolve()
    if not artifact_path.is_relative_to(artifact_root):
        raise HTTPException(status_code=403, detail="Artifact path is outside job root.")
    return artifact_path


def _raise_http_error(exc: Exception) -> None:
    payload = error_payload(exc)
    error_code = payload.get("error_code")
    status_code = 500
    if isinstance(exc, ValidationError):
        status_code = 422
    elif error_code == "JOB_NOT_FOUND":
        status_code = 404
    elif error_code in {
        "EMPTY_URL",
        "LOCAL_PATH_REJECTED",
        "UNSUPPORTED_URL_SCHEME",
        "UNSUPPORTED_GIT_HOST",
        "UNSUPPORTED_SSH_USER",
        "INVALID_GITHUB_REPOSITORY_PATH",
    }:
        status_code = 400
    raise HTTPException(status_code=status_code, detail=payload)


def main() -> None:
    """Run the REST API with Uvicorn."""

    config = get_config()
    uvicorn.run(
        "grna.api.app:create_app",
        factory=True,
        host=config.api_host,
        port=config.api_port,
    )


if __name__ == "__main__":
    main()
