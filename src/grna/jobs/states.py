"""Job state machine definitions."""

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    """Top-level job lifecycle status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStage(StrEnum):
    """Explicit scan and release-note generation stages."""

    QUEUED = "queued"
    FETCHING_REPOSITORY = "fetching_repository"
    INDEXING_EVIDENCE = "indexing_evidence"
    ANALYZING_TECHNOLOGY = "analyzing_technology"
    ANALYZING_CODE = "analyzing_code"
    ANALYZING_INTERFACES = "analyzing_interfaces"
    ANALYZING_COMMITS = "analyzing_commits"
    ANALYZING_TESTS = "analyzing_tests"
    ANALYZING_SPECS = "analyzing_specs"
    GENERATING_DIAGRAMS = "generating_diagrams"
    GENERATING_RELEASE_NOTE = "generating_release_note"
    RENDERING_ARTIFACTS = "rendering_artifacts"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATUSES = {
    JobStatus.COMPLETED,
    JobStatus.FAILED,
    JobStatus.CANCELLED,
}

STAGE_STATUS: dict[JobStage, JobStatus] = {
    JobStage.QUEUED: JobStatus.QUEUED,
    JobStage.FETCHING_REPOSITORY: JobStatus.RUNNING,
    JobStage.INDEXING_EVIDENCE: JobStatus.RUNNING,
    JobStage.ANALYZING_TECHNOLOGY: JobStatus.RUNNING,
    JobStage.ANALYZING_CODE: JobStatus.RUNNING,
    JobStage.ANALYZING_INTERFACES: JobStatus.RUNNING,
    JobStage.ANALYZING_COMMITS: JobStatus.RUNNING,
    JobStage.ANALYZING_TESTS: JobStatus.RUNNING,
    JobStage.ANALYZING_SPECS: JobStatus.RUNNING,
    JobStage.GENERATING_DIAGRAMS: JobStatus.RUNNING,
    JobStage.GENERATING_RELEASE_NOTE: JobStatus.RUNNING,
    JobStage.RENDERING_ARTIFACTS: JobStatus.RUNNING,
    JobStage.COMPLETED: JobStatus.COMPLETED,
    JobStage.FAILED: JobStatus.FAILED,
    JobStage.CANCELLED: JobStatus.CANCELLED,
}

VALID_STAGE_TRANSITIONS: dict[JobStage, set[JobStage]] = {
    JobStage.QUEUED: {
        JobStage.FETCHING_REPOSITORY,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.FETCHING_REPOSITORY: {
        JobStage.INDEXING_EVIDENCE,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.INDEXING_EVIDENCE: {
        JobStage.ANALYZING_TECHNOLOGY,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.ANALYZING_TECHNOLOGY: {
        JobStage.ANALYZING_CODE,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.ANALYZING_CODE: {
        JobStage.ANALYZING_INTERFACES,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.ANALYZING_INTERFACES: {
        JobStage.ANALYZING_COMMITS,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.ANALYZING_COMMITS: {
        JobStage.ANALYZING_TESTS,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.ANALYZING_TESTS: {
        JobStage.ANALYZING_SPECS,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.ANALYZING_SPECS: {
        JobStage.GENERATING_DIAGRAMS,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.GENERATING_DIAGRAMS: {
        JobStage.GENERATING_RELEASE_NOTE,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.GENERATING_RELEASE_NOTE: {
        JobStage.RENDERING_ARTIFACTS,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.RENDERING_ARTIFACTS: {
        JobStage.COMPLETED,
        JobStage.FAILED,
        JobStage.CANCELLED,
    },
    JobStage.COMPLETED: set(),
    JobStage.FAILED: set(),
    JobStage.CANCELLED: set(),
}


def parse_stage(stage: JobStage | str) -> JobStage:
    """Normalize a stage value."""

    if isinstance(stage, JobStage):
        return stage
    return JobStage(stage)


def status_for_stage(stage: JobStage | str) -> JobStatus:
    """Return the top-level status implied by a stage."""

    return STAGE_STATUS[parse_stage(stage)]


def is_valid_transition(current_stage: JobStage | str, next_stage: JobStage | str) -> bool:
    """Return whether the transition is allowed by the state machine."""

    current = parse_stage(current_stage)
    target = parse_stage(next_stage)
    return target in VALID_STAGE_TRANSITIONS[current]
