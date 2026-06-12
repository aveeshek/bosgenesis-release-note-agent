import pytest

from grna.jobs import InvalidJobTransitionError, JobOrchestrator, JobStage, is_valid_transition
from grna.storage.local import LocalJsonJobStore


def _orchestrator(tmp_path) -> JobOrchestrator:
    return JobOrchestrator(LocalJsonJobStore(tmp_path / "jobs"))


def test_state_machine_allows_expected_forward_transitions() -> None:
    assert is_valid_transition(JobStage.QUEUED, JobStage.FETCHING_REPOSITORY)
    assert is_valid_transition(JobStage.FETCHING_REPOSITORY, JobStage.INDEXING_EVIDENCE)
    assert is_valid_transition(JobStage.RENDERING_ARTIFACTS, JobStage.COMPLETED)


def test_state_machine_rejects_invalid_transition(tmp_path) -> None:
    orchestrator = _orchestrator(tmp_path)
    job = orchestrator.create_job(
        repo_url="https://github.com/example/project",
        job_id="scan_invalid",
    )

    with pytest.raises(InvalidJobTransitionError):
        orchestrator.transition_to(job.job_id, JobStage.COMPLETED)

    persisted = orchestrator.get_job(job.job_id)
    assert persisted.status == "queued"
    assert persisted.stage == "queued"


def test_orchestrator_updates_stage_status_and_progress(tmp_path) -> None:
    orchestrator = _orchestrator(tmp_path)
    job = orchestrator.create_job(
        repo_url="https://github.com/example/project",
        payload={"analysis_depth": "standard"},
        job_id="scan_progress",
    )

    updated = orchestrator.transition_to(
        job.job_id,
        JobStage.FETCHING_REPOSITORY,
        progress_percent=10,
    )

    assert updated.status == "running"
    assert updated.stage == "fetching_repository"
    assert updated.progress_percent == 10
    assert updated.updated_at >= updated.created_at

    progressed = orchestrator.update_progress(job.job_id, 25)
    assert progressed.progress_percent == 25
    assert progressed.stage == "fetching_repository"


def test_failure_preserves_error_code_and_message(tmp_path) -> None:
    orchestrator = _orchestrator(tmp_path)
    job = orchestrator.create_job(
        repo_url="https://github.com/example/project",
        job_id="scan_failure",
    )
    orchestrator.transition_to(job.job_id, JobStage.FETCHING_REPOSITORY)

    failed = orchestrator.fail_job(
        job.job_id,
        error_code="FETCH_FAILED",
        error_message="Repository could not be fetched.",
    )

    assert failed.status == "failed"
    assert failed.stage == "failed"
    assert failed.error_code == "FETCH_FAILED"
    assert failed.error_message == "Repository could not be fetched."


def test_terminal_jobs_reject_further_transitions(tmp_path) -> None:
    orchestrator = _orchestrator(tmp_path)
    job = orchestrator.create_job(
        repo_url="https://github.com/example/project",
        job_id="scan_terminal",
    )
    orchestrator.cancel_job(job.job_id)

    with pytest.raises(InvalidJobTransitionError):
        orchestrator.transition_to(job.job_id, JobStage.FETCHING_REPOSITORY)


def test_progress_must_be_between_zero_and_one_hundred(tmp_path) -> None:
    orchestrator = _orchestrator(tmp_path)
    job = orchestrator.create_job(
        repo_url="https://github.com/example/project",
        job_id="scan_bad_progress",
    )

    with pytest.raises(ValueError):
        orchestrator.update_progress(job.job_id, 101)
