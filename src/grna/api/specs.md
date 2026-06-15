# API Module Specification

## Intent

Expose the release-note agent through a REST API suitable for UI clients, automation systems, and CI/CD workflows.

## Role

- Own FastAPI application creation and route registration.
- Validate incoming scan requests.
- Submit jobs to the orchestration layer.
- Return job status, analytics, artifact metadata, and downloadable artifacts.
- Provide health and readiness endpoints.

## Inputs

- HTTP requests for scan creation, job status, analytics, artifact listing, and artifact download.
- JSON payloads containing repository URL, refs, release name, output formats, and analysis depth.
- Repository validation and fetch errors from the GitHub module.
- Application dependencies such as job orchestrator, storage adapters, and configuration.
- Job state transition requests from future worker or operator paths.

## Outputs

- Structured JSON success responses.
- Structured JSON error responses with stable error codes.
- Artifact streams or artifact metadata.
- Health and readiness status.

## Expected Endpoints

- `GET /health`
- `GET /ready`
- `POST /api/v1/scans`
- `GET /api/v1/scans/{job_id}`
- `GET /api/v1/scans/{job_id}/analytics`
- `GET /api/v1/scans/{job_id}/artifacts`
- `GET /api/v1/scans/{job_id}/artifacts/{artifact_id}`
- `GET /api/v1/scans/{job_id}/artifacts/{artifact_id}/download`

## Implemented REST MVP Contract

- `create_app()` builds the FastAPI application and accepts an optional `ReleaseNoteMcpTools` instance for tests and future dependency injection.
- `POST /api/v1/scans` validates the public GitHub URL, runs the shared MVP
  end-to-end pipeline, persists generated artifacts, and returns HTTP `202`
  with completed job metadata when successful.
- `GET /api/v1/scans/{job_id}` returns persisted job status from the shared job store.
- `GET /api/v1/scans/{job_id}/analytics` returns generated analytics JSON when the analytics artifact exists.
- `GET /api/v1/scans/{job_id}/artifacts` returns artifact metadata, optionally filtered by `artifact_type`.
- `GET /api/v1/scans/{job_id}/artifacts/{artifact_id}` returns metadata for a single artifact.
- `GET /api/v1/scans/{job_id}/artifacts/{artifact_id}/download` streams the artifact file only after verifying it remains under the job artifact root.
- REST errors map shared MCP/job/storage validation failures to stable HTTP responses with structured `detail.error_code` payloads.

## Design Rules

- Request handlers must delegate repository analysis to the shared runtime
  pipeline; future worker mode can move the same pipeline behind an async queue.
- API schemas must be explicit and versioned.
- API and MCP paths must share the same core services.
- Errors must include `error_code`, `message`, optional `details`, and `retryable`.
- Artifact downloads must be constrained to the configured artifact root.
- API routes that mutate job state must use the shared `JobOrchestrator`.
- API scan creation must validate GitHub URLs before enqueueing fetch work.
- Artifact lookup and download routes should remain job-scoped so callers cannot enumerate unrelated job artifacts by opaque ID alone.
