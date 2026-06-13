# MCP Module Specification

## Intent

Expose the agent as an MCP-compatible tool server so Codex, Kiro, Claude Code, BOS Genesis agents, and other MCP clients can start scans and retrieve release intelligence artifacts.

## Role

- Define MCP tool schemas.
- Map tool calls to the shared application service layer.
- Return deterministic, structured tool responses.
- Avoid heavy work inside tool handlers by creating jobs and returning job IDs.
- Use the job orchestrator for job creation and cancellation.

## Inputs

- MCP tool calls with JSON arguments.
- Repository scan parameters such as `repo_url`, `branch`, `tag`, `commit_sha`, `release_name`, `analysis_depth`, and `output_formats`.
- Job and artifact lookup arguments.
- Stable GitHub URL validation errors when repository inputs are unsafe.

## Outputs

- Job creation response with `job_id`, status, and message.
- Job status response with stage and progress.
- Analytics bundle response.
- Evidence listing response.
- Diagram inventory response.
- Artifact metadata response.

## Expected Tools

- `github_release_scan_start`
- `github_release_scan_status`
- `github_release_get_analytics`
- `github_release_generate_note`
- `github_release_get_artifact`
- `github_release_list_evidence`
- `github_release_get_diagrams`

## Design Rules

- MCP tool schemas must match REST contracts where possible.
- Tool handlers must validate inputs before delegating.
- MCP mode must be able to run without REST mode.
- Tool responses must not leak local secrets or unrestricted paths.
- Long-running work must be represented as async jobs.
- Invalid job state transitions must return stable structured errors.
- MCP scan tools must use the same GitHub URL validation path as REST and CLI.
