# Storage Module Specification

## Intent

Persist jobs, evidence, analytics, generated artifacts, and audit data.

## Role

- Provide storage adapters for PostgreSQL and local artifact filesystem.
- Store job lifecycle data and stage history.
- Store normalized evidence and analytics JSON.
- Store artifact metadata and checksums.
- Provide safe artifact path resolution.
- Persist job `error_code` and `error_message` for failed jobs.

## Inputs

- Job records.
- Job state machine updates.
- Evidence items.
- Analytics bundles.
- Diagram and report artifacts.
- Configuration for database URL, artifact root, and workspace root.
- Repository workspace metadata files such as `fetch_metadata.json`.

## Outputs

- Persisted records and lookup results.
- Job status, stage, progress, and failure details.
- Artifact paths constrained to configured roots.
- Workspace paths constrained to configured roots.
- Checksums and metadata for generated files.
- Migration definitions through the migrations submodule.

## Expected Logical Tables

- `scan_jobs`
- `scan_stages`
- `evidence_items`
- `analysis_results`
- `generated_artifacts`
- `audit_events`

## Design Rules

- Storage APIs must hide backend-specific details from analyzers and reports.
- Artifact paths must be sanitized and root-bound.
- Database writes should be transactional for job state transitions.
- Partial scan results should be persistable.
- Secrets must not be stored in plaintext evidence or artifacts.
- JSON-backed job records must remain compatible with future PostgreSQL storage.
