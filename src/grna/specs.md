# GRNA Package Specification

## Intent

`grna` is the application package for the GitHub Release Note Intelligence Agent. It coordinates REST, MCP, CLI, async job orchestration, repository fetching, evidence extraction, analytics, diagram generation, report rendering, persistence, and observability.

The package must implement an evidence-first system: repository facts are collected and normalized before any narrative release-note text is generated.

## Role

- Provide the shared application boundary for all runtime modes.
- Keep core behavior reusable across REST API, MCP tools, CLI, and workers.
- Enforce safety rules for public repository analysis.
- Preserve traceability between generated claims and source evidence.

## Inputs

- Public GitHub repository URL.
- Optional branch, tag, commit SHA, or release range.
- Scan options such as analysis depth and requested output formats.
- Runtime configuration from environment variables and config files.
- Local Git fixtures for repository-fetcher tests only.

## Outputs

- Scan job status and stage progression.
- Explicit job state transitions with progress and failure details.
- Repository fetch metadata with resolved commit SHA and default branch.
- Repository inventory and normalized evidence.
- Analytics bundles for technology, intent, features, code, interfaces, commits, tests, coverage, and specs.
- Mermaid/C4/deployment diagram artifacts.
- Markdown, HTML, PDF, JSON, and supporting artifact metadata.

## Design Rules

- Do not execute untrusted repository code by default.
- Reject local filesystem paths in public GitHub URL validation.
- Clone repositories into job-specific isolated workspaces.
- Keep analyzers modular and independently testable.
- Inventory analysis must be deterministic and must skip generated, dependency, and cache folders.
- Technology analysis must include confidence and evidence references for each finding.
- Documentation analysis must distinguish stated project intent from inferred intent and explicit gaps.
- Commit analysis must keep uncategorized commits explicit and avoid fabricated categories.
- Code and interface analysis must remain read-only and report partial-analysis gaps.
- Test and coverage analysis must report coverage only when report evidence exists.
- Analytics aggregation must produce one JSON-ready bundle with normalized gaps and evidence references.
- Diagram generation must include captions, confidence, and explicit gaps for missing evidence.
- Markdown report generation must preserve required sections, Mermaid diagrams, and evidence traceability.
- HTML report generation must use configurable BOS Genesis theme tokens and remain self-contained for offline viewing and PDF conversion.
- PDF report generation must prefer the styled HTML report as its source, preserve report identity, page numbers, compact tables, diagrams/source, and return structured fallback metadata on render failure.
- Evidence indexing must attach stable IDs and redact sensitive values before report generation.
- Use structured models for contracts crossing module boundaries.
- Keep REST, MCP, and CLI as adapters over the same service layer.
- Keep job lifecycle changes behind the shared job orchestrator.
- Every major generated claim must reference evidence where possible.
- Missing data must be reported explicitly, not hidden.
