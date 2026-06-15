# MCP Module Specification

## Intent

Expose the agent as an MCP-compatible tool server so Codex, Kiro, Claude Code, BOS Genesis agents, and other MCP clients can start scans and retrieve release intelligence artifacts.

## Role

- Define MCP tool schemas.
- Map tool calls to the shared application service layer.
- Return deterministic, structured tool responses.
- Run the MVP end-to-end scan pipeline for scan and release-note submission tools.
- Use the job orchestrator for job creation and cancellation.

## Inputs

- MCP tool calls with JSON arguments.
- Repository scan parameters such as `repo_url`, `branch`, `tag`, `commit_sha`, `release_name`, `analysis_depth`, and `output_formats`.
- Job and artifact lookup arguments.
- Stable GitHub URL validation errors when repository inputs are unsafe.

## Outputs

- Job response with `job_id`, status, progress, and generated artifact metadata.
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
- `github_release_note_submit_job`
- `github_release_note_get_job_status`
- `github_release_note_list_artifacts`
- `scan_github_repository`

## Design Rules

- MCP tool schemas must match REST contracts where possible.
- Tool handlers must validate inputs before delegating.
- MCP mode must be able to run without REST mode.
- Tool responses must not leak local secrets or unrestricted paths.
- Canonical `github_release_scan_start` may execute synchronously for REST/API
  compatibility.
- LLD-style submit tools such as `github_release_note_submit_job` and
  `scan_github_repository` must return a queued `job_id` immediately and run the
  scan in the background so MCP clients can poll status and artifacts without
  ingress timeouts.
- Invalid job state transitions must return stable structured errors.
- MCP scan tools must use the same GitHub URL validation path as REST and CLI.
- Analytics, evidence, and artifact tools must read generated artifacts from the
  configured artifact store rather than returning placeholders.
