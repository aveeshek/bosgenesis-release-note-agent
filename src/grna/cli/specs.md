# CLI Module Specification

## Intent

Provide a local developer and operator interface for starting scans, checking job status, debugging analyzers, and generating reports without using HTTP or MCP directly.

## Role

- Expose command-line commands for common workflows.
- Reuse the same service layer as API and MCP.
- Help developers run individual modules during implementation and testing.

## Inputs

- Command-line arguments for repository URL, refs, output formats, workspace path, and analysis depth.
- Environment variables and local configuration.

## Outputs

- Human-readable terminal status.
- Optional JSON output for automation.
- Local artifact paths for generated reports.
- Non-zero process exit codes on failure.

## Expected Commands

- `scan`
- `status`
- `generate-note`
- `analytics`
- `artifact`
- `analyze-module`

## Implemented MVP Commands

- `scan <repo_url>` clones a public GitHub repository into an isolated job workspace,
  runs the local analyzer pipeline, writes analytics/evidence/report artifacts, and marks
  the job completed or failed in the local job store.
- `scan <repo_url> --local-repo <path>` is an explicit local-fixture mode for development
  and tests. It does not weaken public GitHub URL validation for normal scan input.
- `status <job_id>` reads `data/jobs/{job_id}.json` and the artifact manifest for that job.
- `generate-note <analytics.json>` renders Markdown/HTML/PDF report files from a local
  analytics bundle, with optional evidence JSON for appendix enrichment.
- All MVP commands support `--json` for automation-friendly output.

## Design Rules

- The CLI must not bypass validation or security controls.
- CLI output should support both plain text and JSON.
- Commands should be thin adapters over core services.
- Developer-only debug commands must be clearly separated from normal user commands.
- Errors must return non-zero exit codes and stable JSON fields when `--json` is used.
