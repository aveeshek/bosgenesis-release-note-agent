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

## Outputs

- Scan job status and stage progression.
- Repository inventory and normalized evidence.
- Analytics bundles for technology, intent, features, code, interfaces, commits, tests, coverage, and specs.
- Mermaid/C4/deployment diagram artifacts.
- Markdown, HTML, PDF, JSON, and supporting artifact metadata.

## Design Rules

- Do not execute untrusted repository code by default.
- Keep analyzers modular and independently testable.
- Use structured models for contracts crossing module boundaries.
- Keep REST, MCP, and CLI as adapters over the same service layer.
- Every major generated claim must reference evidence where possible.
- Missing data must be reported explicitly, not hidden.

