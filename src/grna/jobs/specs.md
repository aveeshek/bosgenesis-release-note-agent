# Jobs Module Specification

## Intent

Manage asynchronous scan and release-note generation workflows from job creation through completion, failure, or cancellation.

## Role

- Own job state machine and stage transitions.
- Create job records.
- Dispatch work to queue or local async workers.
- Coordinate repository fetch, analyzer pipeline, diagram generation, report generation, and artifact persistence.
- Track progress, warnings, and errors.

## Inputs

- Validated scan request.
- GitHub fetch metadata from the repository module.
- Runtime configuration for queue, workspace, artifact storage, and limits.
- Worker execution events and analyzer results.

## Outputs

- Job IDs.
- Job status snapshots.
- Stage progress events.
- Persisted job state and errors.
- Final artifact references.
- Validation errors for invalid state transitions.

## Expected Stages

- `queued`
- `fetching_repository`
- `indexing_evidence`
- `analyzing_technology`
- `analyzing_code`
- `analyzing_interfaces`
- `analyzing_commits`
- `analyzing_tests`
- `analyzing_specs`
- `generating_diagrams`
- `generating_release_note`
- `rendering_artifacts`
- `completed`
- `failed`
- `cancelled`

## Design Rules

- State transitions must be explicit and testable.
- Valid transitions are defined in `states.py`; terminal jobs cannot move to new stages.
- The orchestrator must be storage-backend agnostic and operate through `JobStore`.
- Progress updates must stay between 0 and 100.
- Failure handling must preserve both `error_code` and `error_message`.
- Jobs must be resumable or safely fail with useful errors where possible.
- Request threads and MCP handlers must not block on full scans.
- Every stage should emit structured logs and audit events.
- Failures must preserve partial evidence when safe.

## Implemented Foundation

- `JobStatus` defines `queued`, `running`, `completed`, `failed`, and `cancelled`.
- `JobStage` defines the explicit scan and generation stages.
- `JobOrchestrator` creates jobs, transitions stages, updates progress, completes,
  fails, and cancels jobs.
- Invalid transitions raise `InvalidJobTransitionError`.
- Later worker tasks should move jobs through `fetching_repository` only after
  `RepositoryFetcher` has produced fetch metadata.
