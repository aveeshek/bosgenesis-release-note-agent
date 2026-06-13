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
- Local Git fixture path for tests only, bypassing public URL validation explicitly.

## Outputs

- Local repository workspace path.
- Fetch metadata including URL, selected ref, resolved commit SHA, timestamp, and default branch.
- Tag and branch metadata.
- Commit history records and changed-file summaries.
- Stable validation and fetch error payloads.

## Design Rules

- Do not execute repository scripts, hooks, package managers, or tests.
- Clone into job-specific isolated workspaces.
- Do not reuse workspaces unless caching is explicitly designed.
- Block local path injection and unsupported URL schemes.
- Normalize accepted URLs to `owner/repo`, `https://github.com/{owner}/{repo}`,
  and `https://github.com/{owner}/{repo}.git`.
- Enforce timeout, size, and file-count limits.
- Redact credentials if they appear in URLs or metadata.
- Repository fetch must disable submodule recursion, Git LFS smudge, interactive
  prompts, and inherited Git templates.
- Branch, tag, and commit SHA are mutually exclusive until an explicit precedence
  rule is designed.

## Implemented Foundation

- `validate_github_url` accepts HTTPS, SSH, and SCP-like GitHub repository URLs.
- Local paths, `file://`, non-GitHub hosts, unsupported schemes, and non-root
  repository URLs are rejected with stable error codes.
- `RepositoryFetcher` clones into `data/workspaces/{job_id}/repo`.
- `fetch_metadata.json` records source URL, redacted URL, default branch,
  selected ref, resolved commit SHA, and timestamp.
