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
- Runtime configuration for queue, workspace, artifact storage, and limits.
- Worker execution events and analyzer results.

## Outputs

- Job IDs.
- Job status snapshots.
- Stage progress events.
- Persisted job state and errors.
- Final artifact references.

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
- Jobs must be resumable or safely fail with useful errors where possible.
- Request threads and MCP handlers must not block on full scans.
- Every stage should emit structured logs and audit events.
- Failures must preserve partial evidence when safe.

