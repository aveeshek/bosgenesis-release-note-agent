"""Job orchestration skeleton and state update helpers."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from grna.storage.interfaces import JobStore
from grna.storage.models import JobRecord, utc_now_iso

from .states import JobStage, is_valid_transition, parse_stage, status_for_stage


class InvalidJobTransitionError(ValueError):
    """Raised when a job stage transition is not allowed."""

    def __init__(self, job_id: str, current_stage: str, next_stage: str) -> None:
        self.job_id = job_id
        self.current_stage = current_stage
        self.next_stage = next_stage
        super().__init__(
            f"invalid transition for {job_id}: {current_stage} -> {next_stage}"
        )


class JobOrchestrator:
    """Foundation job lifecycle coordinator.

    This orchestrator only persists state transitions for now. Worker dispatch and
    analyzer execution will be added by later tasks.
    """

    def __init__(self, job_store: JobStore) -> None:
        self.job_store = job_store

    def create_job(
        self,
        repo_url: str,
        payload: dict | None = None,
        job_id: str | None = None,
    ) -> JobRecord:
        """Create and persist a queued scan job."""

        job = JobRecord.new(
            job_id=job_id or f"scan_{uuid4().hex}",
            repo_url=repo_url,
            payload=payload,
        )
        return self.job_store.save(job)

    def get_job(self, job_id: str) -> JobRecord:
        """Load a job by ID."""

        return self.job_store.get(job_id)

    def transition_to(
        self,
        job_id: str,
        next_stage: JobStage | str,
        progress_percent: int | None = None,
    ) -> JobRecord:
        """Move a job to the next explicit stage."""

        job = self.job_store.get(job_id)
        current_stage = parse_stage(job.stage)
        target_stage = parse_stage(next_stage)
        if not is_valid_transition(current_stage, target_stage):
            raise InvalidJobTransitionError(job.job_id, current_stage.value, target_stage.value)

        return self._save_update(
            job,
            stage=target_stage.value,
            status=status_for_stage(target_stage).value,
            progress_percent=self._resolve_progress(job.progress_percent, progress_percent),
            error_code=None,
            error_message=None,
        )

    def update_progress(
        self,
        job_id: str,
        progress_percent: int,
        stage: JobStage | str | None = None,
    ) -> JobRecord:
        """Update progress and optionally move to a valid next stage."""

        self._assert_progress(progress_percent)
        if stage is not None:
            return self.transition_to(job_id, stage, progress_percent=progress_percent)

        job = self.job_store.get(job_id)
        current_stage = parse_stage(job.stage)
        if status_for_stage(current_stage).value != job.status or job.status in {
            "completed",
            "failed",
            "cancelled",
        }:
            raise InvalidJobTransitionError(job.job_id, job.stage, job.stage)
        return self._save_update(job, progress_percent=progress_percent)

    def complete_job(self, job_id: str) -> JobRecord:
        """Mark a rendering job as completed."""

        return self.transition_to(job_id, JobStage.COMPLETED, progress_percent=100)

    def fail_job(self, job_id: str, error_code: str, error_message: str) -> JobRecord:
        """Mark a job as failed while preserving error details."""

        job = self.job_store.get(job_id)
        current_stage = parse_stage(job.stage)
        if not is_valid_transition(current_stage, JobStage.FAILED):
            raise InvalidJobTransitionError(job.job_id, current_stage.value, JobStage.FAILED.value)
        return self._save_update(
            job,
            status="failed",
            stage="failed",
            error_code=error_code,
            error_message=error_message,
        )

    def cancel_job(self, job_id: str) -> JobRecord:
        """Mark a queued or running job as cancelled."""

        return self.transition_to(job_id, JobStage.CANCELLED)

    def _save_update(self, job: JobRecord, **changes: object) -> JobRecord:
        updated = replace(job, updated_at=utc_now_iso(), **changes)
        return self.job_store.save(updated)

    @staticmethod
    def _resolve_progress(current: int, progress_percent: int | None) -> int:
        if progress_percent is None:
            return current
        JobOrchestrator._assert_progress(progress_percent)
        return progress_percent

    @staticmethod
    def _assert_progress(progress_percent: int) -> None:
        if progress_percent < 0 or progress_percent > 100:
            raise ValueError("progress_percent must be between 0 and 100")
