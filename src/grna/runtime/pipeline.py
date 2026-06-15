"""End-to-end release-note generation pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from grna.analyzers.code_structure import CodeStructureAnalyzer
from grna.analyzers.commits import CommitAnalyzer
from grna.analyzers.documentation import DocumentationAnalyzer
from grna.analyzers.interfaces import InterfaceAnalyzer
from grna.analyzers.inventory import RepositoryInventoryAnalyzer
from grna.analyzers.readiness import ReadinessAnalyzer
from grna.analyzers.technology import TechnologyAnalyzer
from grna.analyzers.test_coverage import TestCoverageAnalyzer
from grna.config import AppConfig, get_config
from grna.diagrams import MermaidDiagramGenerator
from grna.evidence.aggregator import AnalyticsAggregator, AnalyticsBundle, AnalyticsSection
from grna.evidence.indexer import EvidenceIndexer
from grna.evidence.models import EvidenceIndex, EvidenceRecord
from grna.github import RepositoryFetcher
from grna.jobs import JobOrchestrator, JobStage
from grna.observability import ObservabilityRun, ObservabilityService, ObservabilitySettings
from grna.reports import (
    HtmlReleaseNoteRenderer,
    MarkdownReleaseNoteRenderer,
    PdfReleaseNoteRenderer,
    ReleaseNoteContent,
)
from grna.storage.interfaces import ArtifactStore, JobStore
from grna.storage.local import JobNotFoundError, LocalArtifactStore, LocalJsonJobStore
from grna.storage.models import ArtifactMetadata


@dataclass(frozen=True, slots=True)
class ScanPipelineRequest:
    """Input for the end-to-end repository scan pipeline."""

    repo_url: str
    branch: str | None = None
    tag: str | None = None
    commit_sha: str | None = None
    release_name: str | None = None
    output_formats: tuple[str, ...] = ("markdown", "html")
    local_repo: Path | None = None
    runtime: str = "service"
    payload_extra: dict[str, Any] | None = None
    job_id: str | None = None


@dataclass(frozen=True, slots=True)
class GenerateNoteRequest:
    """Input for rendering report files from an existing analytics bundle."""

    analytics: AnalyticsBundle
    output_dir: Path
    title: str
    release_name: str
    repository: str
    evidence: EvidenceIndex | None = None
    output_formats: tuple[str, ...] = ("markdown", "html")


def run_end_to_end_scan(
    request: ScanPipelineRequest,
    *,
    config: AppConfig | None = None,
    job_store: JobStore | None = None,
    artifact_store: ArtifactStore | None = None,
) -> dict[str, Any]:
    """Fetch, analyze, render, persist, and return a completed scan result."""

    resolved_config = config or get_config()
    jobs = job_store or LocalJsonJobStore(resolved_config.job_root)
    artifacts = artifact_store or LocalArtifactStore(resolved_config.artifact_root)
    orchestrator = JobOrchestrator(jobs)
    job_payload = {
        "repo_url": request.repo_url,
        "branch": request.branch,
        "tag": request.tag,
        "commit_sha": request.commit_sha,
        "release_name": request.release_name,
        "output_formats": list(request.output_formats),
        "local_repo": str(request.local_repo) if request.local_repo else None,
        "runtime": request.runtime,
        **(request.payload_extra or {}),
    }
    if request.job_id:
        job = save_job_payload(jobs, jobs.get(request.job_id), job_payload)
    else:
        job = orchestrator.create_job(
            repo_url=request.repo_url,
            payload=job_payload,
        )
    observability = ObservabilityService(
        ObservabilitySettings.from_config(resolved_config)
    ).start_run(
        job_id=job.job_id,
        correlation_id=str((request.payload_extra or {}).get("correlation_id") or job.job_id),
        repository=request.repo_url,
        release_name=request.release_name,
        runtime=request.runtime,
        caller=str((request.payload_extra or {}).get("caller") or request.runtime),
    )
    observability.record_event(
        event_type="request_received",
        phase=JobStage.QUEUED.value,
        action="create_scan_job",
        status="ok",
        details={
            "repo_url": request.repo_url,
            "output_formats": list(request.output_formats),
            "branch": request.branch,
            "tag": request.tag,
            "commit_sha_provided": bool(request.commit_sha),
        },
    )

    try:
        fetcher = RepositoryFetcher(
            workspace_root=resolved_config.workspace_root,
            config=resolved_config,
        )
        orchestrator.transition_to(job.job_id, JobStage.FETCHING_REPOSITORY, 5)
        with observability.phase(JobStage.FETCHING_REPOSITORY.value, action="fetch_repository"):
            if request.local_repo is not None:
                fetch_metadata = fetcher.fetch_local_fixture(
                    request.local_repo,
                    job_id=job.job_id,
                    branch=request.branch,
                    tag=request.tag,
                    commit_sha=request.commit_sha,
                )
            else:
                fetch_metadata = fetcher.fetch_public_repository(
                    request.repo_url,
                    job_id=job.job_id,
                    branch=request.branch,
                    tag=request.tag,
                    commit_sha=request.commit_sha,
                )
            observability.record_event(
                event_type="repository_fetched",
                phase=JobStage.FETCHING_REPOSITORY.value,
                action="fetch_repository",
                status="ok",
                details={
                    "default_branch": fetch_metadata.default_branch,
                    "selected_ref": fetch_metadata.selected_ref,
                    "resolved_commit_sha": fetch_metadata.resolved_commit_sha,
                },
            )

        repo_path = Path(fetch_metadata.repo_path)
        orchestrator.transition_to(job.job_id, JobStage.INDEXING_EVIDENCE, 18)
        with observability.phase(JobStage.INDEXING_EVIDENCE.value, action="index_evidence"):
            inventory_raw = RepositoryInventoryAnalyzer().analyze(repo_path)
            inventory, evidence = EvidenceIndexer(job.job_id).index_inventory(inventory_raw)
            observability.record_event(
                event_type="evidence_indexed",
                phase=JobStage.INDEXING_EVIDENCE.value,
                action="index_evidence",
                status="ok",
                details={
                    "file_count": inventory.total_files,
                    "evidence_count": len(evidence.records),
                },
            )

        orchestrator.transition_to(job.job_id, JobStage.ANALYZING_TECHNOLOGY, 30)
        with observability.phase(JobStage.ANALYZING_TECHNOLOGY.value):
            technology = TechnologyAnalyzer().analyze(repo_path, inventory)

        orchestrator.transition_to(job.job_id, JobStage.ANALYZING_CODE, 42)
        with observability.phase(JobStage.ANALYZING_CODE.value):
            code_structure = CodeStructureAnalyzer().analyze(repo_path, inventory)

        orchestrator.transition_to(job.job_id, JobStage.ANALYZING_INTERFACES, 52)
        with observability.phase(JobStage.ANALYZING_INTERFACES.value):
            interfaces = InterfaceAnalyzer().analyze(repo_path, inventory)

        orchestrator.transition_to(job.job_id, JobStage.ANALYZING_COMMITS, 62)
        with observability.phase(JobStage.ANALYZING_COMMITS.value):
            commits = CommitAnalyzer().analyze(repo_path, max_commits=200)

        orchestrator.transition_to(job.job_id, JobStage.ANALYZING_TESTS, 72)
        with observability.phase(JobStage.ANALYZING_TESTS.value):
            test_coverage = TestCoverageAnalyzer().analyze(repo_path, inventory)

        orchestrator.transition_to(job.job_id, JobStage.ANALYZING_SPECS, 80)
        with observability.phase(JobStage.ANALYZING_SPECS.value):
            documentation = DocumentationAnalyzer().analyze(repo_path, inventory)

        with observability.phase("readiness_analysis"):
            readiness = ReadinessAnalyzer(resolved_config).analyze(
                repo_path,
                inventory,
                technology=technology,
                documentation=documentation,
                interfaces=interfaces,
                test_coverage=test_coverage,
            )

        with observability.phase("analytics_aggregation"):
            analytics = AnalyticsAggregator(job.job_id, evidence).aggregate(
                inventory=inventory,
                technology=technology,
                documentation=documentation,
                commits=commits,
                code_structure=code_structure,
                interfaces=interfaces,
                test_coverage=test_coverage,
                readiness=readiness,
            )
            observability.record_warnings(list(analytics.gaps), phase="analytics_aggregation")
            observability.record_release_reasoning(
                {
                    "evidence_ids": len(analytics.evidence_ids),
                    "gap_count": len(analytics.gaps),
                    "warning_count": len(analytics.warnings),
                    "section_count": len(analytics.sections),
                }
            )

        orchestrator.transition_to(job.job_id, JobStage.GENERATING_DIAGRAMS, 86)
        with observability.phase(JobStage.GENERATING_DIAGRAMS.value):
            diagrams = MermaidDiagramGenerator().generate(analytics)
        content = ReleaseNoteContent(
            title=report_title(request.repo_url),
            release_name=request.release_name or release_name(fetch_metadata.selected_ref),
            repository=request.repo_url,
            generated_at=analytics.generated_at,
            analytics=analytics,
            diagrams=diagrams,
            evidence=evidence,
        )

        orchestrator.transition_to(job.job_id, JobStage.GENERATING_RELEASE_NOTE, 92)
        with observability.phase(JobStage.GENERATING_RELEASE_NOTE.value):
            generated_artifacts = save_scan_artifacts(
                artifact_store=artifacts,
                job_id=job.job_id,
                content=content,
                analytics=analytics,
                evidence=evidence,
                fetch_metadata=fetch_metadata.to_dict(),
                output_formats=request.output_formats,
                observability=observability,
            )

        orchestrator.transition_to(job.job_id, JobStage.RENDERING_ARTIFACTS, 98)
        with observability.phase(JobStage.RENDERING_ARTIFACTS.value):
            observability.record_event(
                event_type="response_ready",
                phase=JobStage.RENDERING_ARTIFACTS.value,
                action="complete_scan_job",
                status="ok",
                details={"artifact_count": len(generated_artifacts)},
            )
            observability_artifact = artifacts.save_artifact(
                job.job_id,
                "observability.json",
                json_bytes(observability.summary()),
                "observability",
                "application/json",
            )
            generated_artifacts.append(observability_artifact)
        completed = orchestrator.complete_job(job.job_id)
        completed = save_job_payload(
            jobs,
            completed,
            {
                **(completed.payload or {}),
                "fetch_metadata": fetch_metadata.to_dict(),
                "artifact_count": len(generated_artifacts),
                "observability": observability.summary(),
            },
        )
        return {
            "job_id": completed.job_id,
            "status": completed.status,
            "stage": completed.stage,
            "progress_percent": completed.progress_percent,
            "repository": request.repo_url,
            "resolved_commit_sha": fetch_metadata.resolved_commit_sha,
            "artifacts": [artifact.to_dict() for artifact in generated_artifacts],
            "analytics": {
                "available": True,
                "path": _artifact_path(generated_artifacts, "analytics"),
                "evidence_ids": len(analytics.evidence_ids),
                "gaps": list(analytics.gaps),
            },
            "observability": {
                "available": True,
                "path": _artifact_path(generated_artifacts, "observability"),
                "trace_ids": observability.trace_ids,
            },
        }
    except Exception as exc:
        observability.record_event(
            event_type="scan_failed",
            phase="failure",
            action="run_end_to_end_scan",
            status="failed",
            severity="error",
            message=error_message(exc),
            details={"error_code": error_code(exc)},
        )
        failed = orchestrator.fail_job(job.job_id, error_code(exc), error_message(exc))
        save_job_payload(
            jobs,
            failed,
            {
                **(failed.payload or {}),
                "runtime": request.runtime,
                "observability": observability.summary(),
            },
        )
        raise


def save_scan_artifacts(
    *,
    artifact_store: ArtifactStore,
    job_id: str,
    content: ReleaseNoteContent,
    analytics: AnalyticsBundle,
    evidence: EvidenceIndex,
    fetch_metadata: dict,
    output_formats: tuple[str, ...],
    observability: ObservabilityRun | None = None,
) -> list[ArtifactMetadata]:
    """Persist all generated scan artifacts and return their metadata."""

    artifacts = [
        _save_observed_artifact(
            artifact_store,
            job_id,
            "analytics.json",
            json_bytes(analytics.to_dict()),
            "analytics",
            "application/json",
            observability,
        ),
        _save_observed_artifact(
            artifact_store,
            job_id,
            "evidence.json",
            json_bytes(evidence.to_dict()),
            "evidence",
            "application/json",
            observability,
        ),
        _save_observed_artifact(
            artifact_store,
            job_id,
            "fetch_metadata.json",
            json_bytes(fetch_metadata),
            "metadata",
            "application/json",
            observability,
        ),
    ]
    if "markdown" in output_formats:
        artifacts.append(
            _save_observed_artifact(
                artifact_store,
                job_id,
                "release-note.md",
                MarkdownReleaseNoteRenderer().render(content).encode("utf-8"),
                "markdown",
                "text/markdown",
                observability,
            )
        )
    html = ""
    if "html" in output_formats or "pdf" in output_formats:
        html = HtmlReleaseNoteRenderer().render(content)
    if "html" in output_formats:
        artifacts.append(
            _save_observed_artifact(
                artifact_store,
                job_id,
                "release-note.html",
                html.encode("utf-8"),
                "html",
                "text/html",
                observability,
            )
        )
    if "pdf" in output_formats:
        markdown = MarkdownReleaseNoteRenderer().render(content)
        pdf_result = PdfReleaseNoteRenderer().render(content, html=html, markdown=markdown)
        if pdf_result.ok and pdf_result.pdf_bytes:
            artifacts.append(
                _save_observed_artifact(
                    artifact_store,
                    job_id,
                    "release-note.pdf",
                    pdf_result.pdf_bytes,
                    "pdf",
                    "application/pdf",
                    observability,
                )
            )
        else:
            artifacts.append(
                _save_observed_artifact(
                    artifact_store,
                    job_id,
                    "pdf-render-error.json",
                    json_bytes(
                        {
                            "ok": False,
                            "renderer": pdf_result.renderer,
                            "html_preserved": pdf_result.html_preserved,
                            "markdown_preserved": pdf_result.markdown_preserved,
                            "error_message": pdf_result.error_message
                            or "PDF rendering failed without an error message.",
                        }
                    ),
                    "pdf_error",
                    "application/json",
                    observability,
                )
            )
    return artifacts


def _save_observed_artifact(
    artifact_store: ArtifactStore,
    job_id: str,
    relative_path: str,
    content: bytes,
    artifact_type: str,
    content_type: str | None,
    observability: ObservabilityRun | None,
) -> ArtifactMetadata:
    metadata = artifact_store.save_artifact(
        job_id,
        relative_path,
        content,
        artifact_type,
        content_type,
    )
    if observability is not None:
        observability.record_artifact_generated(
            artifact_type=metadata.artifact_type,
            relative_path=metadata.relative_path,
            size_bytes=metadata.size_bytes,
            checksum_sha256=metadata.checksum_sha256,
        )
    return metadata


def write_report_files(request: GenerateNoteRequest) -> list[Path]:
    """Render Markdown, HTML, and optional PDF files from analytics input."""

    request.output_dir.mkdir(parents=True, exist_ok=True)
    content = ReleaseNoteContent(
        title=request.title,
        release_name=request.release_name,
        repository=request.repository,
        generated_at=request.analytics.generated_at,
        analytics=request.analytics,
        diagrams=MermaidDiagramGenerator().generate(request.analytics),
        evidence=request.evidence,
    )
    written: list[Path] = []
    markdown = ""
    html = ""
    if "markdown" in request.output_formats or "pdf" in request.output_formats:
        markdown = MarkdownReleaseNoteRenderer().render(content)
    if "markdown" in request.output_formats:
        path = request.output_dir / "release-note.md"
        path.write_text(markdown, encoding="utf-8")
        written.append(path)
    if "html" in request.output_formats or "pdf" in request.output_formats:
        html = HtmlReleaseNoteRenderer().render(content)
    if "html" in request.output_formats:
        path = request.output_dir / "release-note.html"
        path.write_text(html, encoding="utf-8")
        written.append(path)
    if "pdf" in request.output_formats:
        pdf_result = PdfReleaseNoteRenderer().render(content, html=html, markdown=markdown)
        if not pdf_result.ok or not pdf_result.pdf_bytes:
            raise RuntimeError(f"PDF rendering failed: {pdf_result.error_message}")
        path = request.output_dir / "release-note.pdf"
        path.write_bytes(pdf_result.pdf_bytes)
        written.append(path)
    return written


def analytics_from_file(path: Path) -> AnalyticsBundle:
    """Load an analytics bundle from JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    sections = {
        name: AnalyticsSection(
            name=section.get("name", name),
            data=section.get("data", {}),
            gaps=tuple(section.get("gaps", [])),
            warnings=tuple(section.get("warnings", [])),
            evidence_ids=tuple(section.get("evidence_ids", [])),
        )
        for name, section in payload.get("sections", {}).items()
    }
    return AnalyticsBundle(
        job_id=payload["job_id"],
        generated_at=payload["generated_at"],
        sections=sections,
        gaps=tuple(payload.get("gaps", [])),
        warnings=tuple(payload.get("warnings", [])),
        evidence_ids=tuple(payload.get("evidence_ids", [])),
    )


def evidence_from_file(path: Path) -> EvidenceIndex:
    """Load an evidence index from JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return EvidenceIndex(
        tuple(EvidenceRecord(**record) for record in payload.get("records", []))
    )


def save_job_payload(store: JobStore, job, payload: dict) -> object:
    """Persist a job with an updated payload."""

    return store.save(replace(job, payload=payload))


def json_bytes(payload: dict) -> bytes:
    """Return deterministic JSON bytes for artifact storage."""

    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def report_title(repo_url: str) -> str:
    """Return a readable report title from a repository URL."""

    repo_name = repo_url.rstrip("/").rsplit("/", maxsplit=1)[-1]
    return f"{repo_name.replace('-', ' ').title()} Release Notes"


def release_name(selected_ref: str | None) -> str:
    """Return a fallback release name."""

    return selected_ref or "current"


def error_code(exc: Exception) -> str:
    """Return a stable pipeline error code."""

    if isinstance(exc, JobNotFoundError):
        return "JOB_NOT_FOUND"
    return getattr(exc, "error_code", exc.__class__.__name__.upper())


def error_message(exc: Exception) -> str:
    """Return a useful pipeline error message."""

    if hasattr(exc, "to_dict"):
        payload = exc.to_dict()
        details = payload.get("details") or {}
        if details:
            detail_text = json.dumps(details, sort_keys=True)
            return f"{payload.get('message', str(exc))} Details: {detail_text}"
        return str(payload.get("message", str(exc)))
    return str(exc)


def _artifact_path(artifacts: list[ArtifactMetadata], artifact_type: str) -> str | None:
    for artifact in artifacts:
        if artifact.artifact_type == artifact_type:
            return artifact.path
    return None
