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
- `analytics`
- `artifact`
- `generate-note`
- `analyze-module`

## Design Rules

- The CLI must not bypass validation or security controls.
- CLI output should support both plain text and JSON.
- Commands should be thin adapters over core services.
- Developer-only debug commands must be clearly separated from normal user commands.

