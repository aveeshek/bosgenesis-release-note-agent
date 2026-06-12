"""MCP tool handlers backed by local storage interfaces."""

from __future__ import annotations

from uuid import uuid4

from pydantic import ValidationError

from grna.config import AppConfig, get_config
from grna.jobs import InvalidJobTransitionError, JobOrchestrator
from grna.storage import ArtifactStore, JobNotFoundError, JobStore
from grna.storage.local import LocalArtifactStore, LocalJsonJobStore

from .schemas import (
    TOOL_SCHEMAS,
    AnalyzerOnlyRequest,
    ArtifactLookupRequest,
    JobLookupRequest,
    ReleaseNoteSubmitRequest,
    ScanStartRequest,
)


class ToolExecutionError(ValueError):
    """Raised when a tool cannot be executed."""


def create_default_job_store(config: AppConfig | None = None) -> JobStore:
    """Create the configured job store implementation."""

    resolved_config = config or get_config()
    return LocalJsonJobStore(resolved_config.job_root)


def create_default_artifact_store(config: AppConfig | None = None) -> ArtifactStore:
    """Create the configured artifact store implementation."""

    resolved_config = config or get_config()
    return LocalArtifactStore(resolved_config.artifact_root)


class ReleaseNoteMcpTools:
    """Callable tool surface for MCP adapters and HTTP access."""

    def __init__(
        self,
        job_store: JobStore | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.job_store = job_store or create_default_job_store()
        self.artifact_store = artifact_store or create_default_artifact_store()
        self.orchestrator = JobOrchestrator(self.job_store)

    def list_tools(self) -> dict[str, dict]:
        """Return available tool schemas."""

        return TOOL_SCHEMAS

    def invoke(self, tool_name: str, arguments: dict) -> dict:
        """Invoke a tool by name with JSON-compatible arguments."""

        tool_map = {
            "github_release_scan_start": self.github_release_scan_start,
            "github_release_scan_status": self.github_release_scan_status,
            "github_release_get_analytics": self.github_release_get_analytics,
            "github_release_generate_note": self.github_release_generate_note,
            "github_release_get_artifact": self.github_release_get_artifact,
            "github_release_list_evidence": self.github_release_list_evidence,
            "github_release_get_diagrams": self.github_release_get_diagrams,
            "github_release_note_submit_job": self.github_release_note_submit_job,
            "github_release_note_get_job_status": self.github_release_note_get_job_status,
            "github_release_note_list_artifacts": self.github_release_note_list_artifacts,
            "github_release_note_get_artifact": self.github_release_note_get_artifact,
            "github_release_note_get_evidence": self.github_release_note_get_evidence,
            "github_release_note_cancel_job": self.github_release_note_cancel_job,
            "github_repo_scan_only": self.github_repo_scan_only,
            "github_commit_analytics_only": self.github_commit_analytics_only,
            "github_code_analytics_only": self.github_code_analytics_only,
            "scan_github_repository": self.scan_github_repository,
            "get_release_note_job_status": self.get_release_note_job_status,
            "get_repository_analysis_summary": self.get_repository_analysis_summary,
            "generate_release_note": self.generate_release_note,
            "get_release_note_artifact": self.get_release_note_artifact,
            "get_release_note_artifacts": self.get_release_note_artifacts,
        }
        handler = tool_map.get(tool_name)
        if handler is None:
            raise ToolExecutionError(f"unknown MCP tool: {tool_name}")
        return handler(arguments)

    def github_release_scan_start(self, arguments: dict) -> dict:
        """Create a queued scan job without performing the long-running scan inline."""

        request = ScanStartRequest.model_validate(arguments)
        job_id = f"scan_{uuid4().hex}"
        job = self.orchestrator.create_job(
            repo_url=request.repo_url,
            job_id=job_id,
            payload=request.model_dump(mode="json"),
        )
        return {
            "job_id": job.job_id,
            "status": job.status,
            "stage": job.stage,
            "message": "Scan job accepted. Repository analysis will run asynchronously.",
        }

    def github_release_scan_status(self, arguments: dict) -> dict:
        """Return job status."""

        request = JobLookupRequest.model_validate(arguments)
        return self.job_store.get(request.job_id).to_dict()

    def github_release_get_analytics(self, arguments: dict) -> dict:
        """Return analytics placeholder until analyzer pipeline is implemented."""

        request = JobLookupRequest.model_validate(arguments)
        job = self.job_store.get(request.job_id)
        return {
            "job_id": job.job_id,
            "status": job.status,
            "available": False,
            "message": "Analytics generation is not implemented yet.",
            "analytics": {},
        }

    def github_release_generate_note(self, arguments: dict) -> dict:
        """Return report generation placeholder until report pipeline is implemented."""

        request = JobLookupRequest.model_validate(arguments)
        job = self.job_store.get(request.job_id)
        return {
            "job_id": job.job_id,
            "available": False,
            "message": "Release-note generation is not implemented yet.",
            "artifacts": [
                artifact.to_dict()
                for artifact in self.artifact_store.list_artifacts(job.job_id)
            ],
        }

    def github_release_get_artifact(self, arguments: dict) -> dict:
        """Return artifact metadata for a job, optionally filtered by type."""

        request = ArtifactLookupRequest.model_validate(arguments)
        self.job_store.get(request.job_id)
        artifacts = self.artifact_store.list_artifacts(request.job_id)
        if request.artifact_type:
            artifacts = [
                artifact
                for artifact in artifacts
                if artifact.artifact_type == request.artifact_type
            ]
        return {
            "job_id": request.job_id,
            "available": bool(artifacts),
            "artifacts": [artifact.to_dict() for artifact in artifacts],
        }

    def github_release_list_evidence(self, arguments: dict) -> dict:
        """Return evidence placeholder until evidence indexing is implemented."""

        request = JobLookupRequest.model_validate(arguments)
        job = self.job_store.get(request.job_id)
        return {
            "job_id": job.job_id,
            "available": False,
            "message": "Evidence indexing is not implemented yet.",
            "evidence": [],
        }

    def github_release_get_diagrams(self, arguments: dict) -> dict:
        """Return diagram artifacts recorded for a job."""

        request = JobLookupRequest.model_validate(arguments)
        self.job_store.get(request.job_id)
        diagrams = [
            artifact.to_dict()
            for artifact in self.artifact_store.list_artifacts(request.job_id)
            if artifact.artifact_type == "diagram"
        ]
        return {
            "job_id": request.job_id,
            "available": bool(diagrams),
            "diagrams": diagrams,
        }

    def github_release_note_submit_job(self, arguments: dict) -> dict:
        """Submit a release-note generation job using the LLD contract."""

        request = ReleaseNoteSubmitRequest.model_validate(arguments)
        output_formats = ["markdown", "html"]
        if request.include_pdf:
            output_formats.append("pdf")
        return self.github_release_scan_start(
            {
                "repo_url": request.repo_url,
                "branch": request.ref or request.to_ref,
                "release_name": request.release_name,
                "analysis_depth": request.analysis_depth,
                "output_formats": output_formats,
                "from_ref": request.from_ref,
                "to_ref": request.to_ref,
                "output_profile": request.output_profile,
                "job_mode": "release_note",
            }
        )

    def github_release_note_get_job_status(self, arguments: dict) -> dict:
        """Alias for the canonical status tool."""

        return self.github_release_scan_status(arguments)

    def github_release_note_list_artifacts(self, arguments: dict) -> dict:
        """List all artifact metadata for a job."""

        request = JobLookupRequest.model_validate(arguments)
        self.job_store.get(request.job_id)
        artifacts = [
            artifact.to_dict()
            for artifact in self.artifact_store.list_artifacts(request.job_id)
        ]
        return {
            "job_id": request.job_id,
            "available": bool(artifacts),
            "artifacts": artifacts,
        }

    def github_release_note_get_artifact(self, arguments: dict) -> dict:
        """Alias for artifact lookup with optional artifact ID filtering."""

        result = self.github_release_get_artifact(arguments)
        artifact_id = ArtifactLookupRequest.model_validate(arguments).artifact_id
        if artifact_id:
            result["artifacts"] = [
                artifact
                for artifact in result["artifacts"]
                if artifact["artifact_id"] == artifact_id
            ]
            result["available"] = bool(result["artifacts"])
        return result

    def github_release_note_get_evidence(self, arguments: dict) -> dict:
        """Return the structured evidence placeholder for a job."""

        result = self.github_release_list_evidence(arguments)
        result["evidence_model"] = {
            "available": False,
            "items": result.pop("evidence", []),
            "message": "Evidence model generation is not implemented yet.",
        }
        return result

    def github_release_note_cancel_job(self, arguments: dict) -> dict:
        """Request cancellation for a job.

        The async worker is not implemented yet, so this updates queued jobs to a terminal
        placeholder state and reports that active cancellation will be wired later.
        """

        request = JobLookupRequest.model_validate(arguments)
        job = self.job_store.get(request.job_id)
        if job.status in {"completed", "failed", "cancelled"}:
            return {
                "job_id": job.job_id,
                "status": job.status,
                "stage": job.stage,
                "cancelled": job.status == "cancelled",
                "message": "Job is already in a terminal state.",
            }
        cancelled_job = self.orchestrator.cancel_job(job.job_id)
        return {
            "job_id": cancelled_job.job_id,
            "status": cancelled_job.status,
            "stage": cancelled_job.stage,
            "cancelled": True,
            "message": "Cancellation recorded locally. Worker cancellation is not implemented yet.",
        }

    def github_repo_scan_only(self, arguments: dict) -> dict:
        """Submit a repository scan only placeholder job."""

        return self._submit_analyzer_only_job(arguments, "repo_scan_only")

    def github_commit_analytics_only(self, arguments: dict) -> dict:
        """Submit a commit analytics only placeholder job."""

        return self._submit_analyzer_only_job(arguments, "commit_analytics_only")

    def github_code_analytics_only(self, arguments: dict) -> dict:
        """Submit a code analytics only placeholder job."""

        return self._submit_analyzer_only_job(arguments, "code_analytics_only")

    def scan_github_repository(self, arguments: dict) -> dict:
        """Plan-contract alias for submitting a repository scan."""

        return self.github_release_note_submit_job(arguments)

    def get_release_note_job_status(self, arguments: dict) -> dict:
        """Plan-contract alias for reading job status."""

        return self.github_release_scan_status(arguments)

    def get_repository_analysis_summary(self, arguments: dict) -> dict:
        """Return a placeholder repository analysis summary."""

        request = JobLookupRequest.model_validate(arguments)
        job = self.job_store.get(request.job_id)
        return {
            "job_id": job.job_id,
            "status": job.status,
            "available": False,
            "message": "Repository analysis summary is not implemented yet.",
            "summary": {},
        }

    def generate_release_note(self, arguments: dict) -> dict:
        """Plan-contract alias for release-note generation."""

        return self.github_release_generate_note(arguments)

    def get_release_note_artifact(self, arguments: dict) -> dict:
        """Plan-contract alias for artifact lookup."""

        return self.github_release_note_get_artifact(arguments)

    def get_release_note_artifacts(self, arguments: dict) -> dict:
        """Plan-contract alias for artifact listing."""

        return self.github_release_note_list_artifacts(arguments)

    def _submit_analyzer_only_job(self, arguments: dict, job_mode: str) -> dict:
        request = AnalyzerOnlyRequest.model_validate(arguments)
        result = self.github_release_scan_start(
            {
                "repo_url": request.repo_url,
                "branch": request.ref or request.to_ref,
                "analysis_depth": request.analysis_depth,
                "output_formats": ["json"],
                "from_ref": request.from_ref,
                "to_ref": request.to_ref,
                "job_mode": job_mode,
            }
        )
        result["job_mode"] = job_mode
        return result


def error_payload(exc: Exception) -> dict:
    """Convert tool errors to stable JSON payloads."""

    if isinstance(exc, ValidationError):
        return {"error_code": "VALIDATION_ERROR", "message": str(exc), "retryable": False}
    if isinstance(exc, JobNotFoundError):
        return {"error_code": "JOB_NOT_FOUND", "message": str(exc), "retryable": False}
    if isinstance(exc, ToolExecutionError):
        return {"error_code": "UNKNOWN_TOOL", "message": str(exc), "retryable": False}
    if isinstance(exc, InvalidJobTransitionError):
        return {
            "error_code": "INVALID_JOB_TRANSITION",
            "message": str(exc),
            "retryable": False,
        }
    return {"error_code": "MCP_TOOL_ERROR", "message": str(exc), "retryable": False}
