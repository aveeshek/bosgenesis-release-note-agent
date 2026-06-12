"""MCP tool request and response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AnalysisDepth = Literal["fast", "standard", "deep"]
OutputFormat = Literal["markdown", "html", "pdf", "json"]


class ScanStartRequest(BaseModel):
    """Input for `github_release_scan_start`."""

    repo_url: str
    branch: str | None = None
    tag: str | None = None
    commit_sha: str | None = None
    release_name: str | None = None
    analysis_depth: AnalysisDepth = "standard"
    output_formats: list[OutputFormat] = Field(default_factory=lambda: ["markdown", "html"])


class ReleaseNoteSubmitRequest(BaseModel):
    """Input for LLD-style release-note job submission tools."""

    repo_url: str
    ref: str | None = None
    from_ref: str | None = None
    to_ref: str | None = None
    include_pdf: bool = True
    output_profile: str = "enterprise"
    release_name: str | None = None
    analysis_depth: AnalysisDepth = "standard"


class JobLookupRequest(BaseModel):
    """Input for job lookup tools."""

    job_id: str


class ArtifactLookupRequest(JobLookupRequest):
    """Input for artifact lookup tools."""

    artifact_type: str | None = None
    artifact_id: str | None = None


class AnalyzerOnlyRequest(BaseModel):
    """Input for analyzer-only placeholder jobs."""

    repo_url: str
    ref: str | None = None
    from_ref: str | None = None
    to_ref: str | None = None
    analysis_depth: AnalysisDepth = "standard"


class ToolResponse(BaseModel):
    """Generic MCP HTTP tool response wrapper."""

    ok: bool
    result: dict
    error: dict | None = None


TOOL_SCHEMAS: dict[str, dict] = {
    "github_release_scan_start": {
        "description": "Start a GitHub release-note scan job.",
        "input_schema": ScanStartRequest.model_json_schema(),
    },
    "github_release_scan_status": {
        "description": "Get scan job status.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "github_release_get_analytics": {
        "description": "Get analytics JSON for a scan job.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "github_release_generate_note": {
        "description": "Generate or regenerate release-note artifacts for a scan job.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "github_release_get_artifact": {
        "description": "Get generated artifact metadata for a scan job.",
        "input_schema": ArtifactLookupRequest.model_json_schema(),
    },
    "github_release_list_evidence": {
        "description": "List evidence references for a scan job.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "github_release_get_diagrams": {
        "description": "Get diagram artifact metadata for a scan job.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "github_release_note_submit_job": {
        "description": "Submit a repo scan and release-note generation job.",
        "input_schema": ReleaseNoteSubmitRequest.model_json_schema(),
    },
    "github_release_note_get_job_status": {
        "description": "Poll current release-note job status.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "github_release_note_list_artifacts": {
        "description": "List generated release-note artifacts.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "github_release_note_get_artifact": {
        "description": (
            "Retrieve release-note artifact metadata, content reference, or download path."
        ),
        "input_schema": ArtifactLookupRequest.model_json_schema(),
    },
    "github_release_note_get_evidence": {
        "description": "Retrieve the structured evidence model for a job.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "github_release_note_cancel_job": {
        "description": "Request cancellation for a queued or running release-note job.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "github_repo_scan_only": {
        "description": "Submit a repository-understanding scan without release-note generation.",
        "input_schema": AnalyzerOnlyRequest.model_json_schema(),
    },
    "github_commit_analytics_only": {
        "description": "Submit a commit analytics only job.",
        "input_schema": AnalyzerOnlyRequest.model_json_schema(),
    },
    "github_code_analytics_only": {
        "description": "Submit a code analytics only job.",
        "input_schema": AnalyzerOnlyRequest.model_json_schema(),
    },
    "scan_github_repository": {
        "description": "Alias for starting a GitHub repository scan.",
        "input_schema": ReleaseNoteSubmitRequest.model_json_schema(),
    },
    "get_release_note_job_status": {
        "description": "Alias for reading release-note job status.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "get_repository_analysis_summary": {
        "description": "Return current repository analysis summary for a job.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "generate_release_note": {
        "description": "Generate or retrieve release-note artifacts for an existing job.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
    "get_release_note_artifact": {
        "description": "Alias for retrieving one release-note artifact reference.",
        "input_schema": ArtifactLookupRequest.model_json_schema(),
    },
    "get_release_note_artifacts": {
        "description": "Alias for listing release-note artifacts.",
        "input_schema": JobLookupRequest.model_json_schema(),
    },
}
