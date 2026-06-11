# GitHub Module Specification

## Intent

Safely fetch and inspect public GitHub repositories as untrusted read-only input.

## Role

- Validate public GitHub repository URLs.
- Clone or fetch repositories into isolated job workspaces.
- Resolve branch, tag, and commit references.
- Collect repository metadata, tags, branches, commit ranges, and release information when available.
- Provide Git history access for commit analytics.

## Inputs

- Public GitHub repository URL.
- Optional branch, tag, commit SHA, or release range.
- Job workspace path.
- Repository size, clone depth, timeout, and file limits.

## Outputs

- Local repository workspace path.
- Fetch metadata including URL, selected ref, resolved commit SHA, timestamp, and default branch.
- Tag and branch metadata.
- Commit history records and changed-file summaries.

## Design Rules

- Do not execute repository scripts, hooks, package managers, or tests.
- Clone into job-specific isolated workspaces.
- Do not reuse workspaces unless caching is explicitly designed.
- Block local path injection and unsupported URL schemes.
- Enforce timeout, size, and file-count limits.
- Redact credentials if they appear in URLs or metadata.

