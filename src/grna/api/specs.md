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
- Application dependencies such as job orchestrator, storage adapters, and configuration.

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
- `GET /api/v1/artifacts/{artifact_id}`

## Design Rules

- Request handlers must not perform long-running repository analysis inline.
- API schemas must be explicit and versioned.
- API and MCP paths must share the same core services.
- Errors must include `error_code`, `message`, optional `details`, and `retryable`.
- Artifact downloads must be constrained to the configured artifact root.

