# Tests Specification

## Intent

Validate that the agent safely scans public repositories, builds evidence-backed analytics, exposes REST and MCP contracts, and generates professional release-note artifacts.

## Role

- Store unit, integration, fixture, contract, and acceptance tests.
- Protect module boundaries defined in `src/grna/**/specs.md`.
- Validate safety rules around untrusted repositories.

## Inputs

- Test fixtures.
- Small public repository examples or local fixture repositories.
- Generated analytics and artifacts.
- REST and MCP request/response samples.

## Outputs

- Test results.
- Coverage reports when enabled.
- Golden files or snapshots for reports and diagrams.

## Test Areas

- URL validation and GitHub fetching.
- Job state transitions.
- Analyzer contracts and evidence references.
- Technology, code, interface, test, coverage, commit, and spec analyzers.
- Diagram generation.
- Markdown, HTML, and PDF report generation.
- REST API contracts.
- MCP tool contracts.
- Security redaction and path safety.

## Design Rules

- Tests must not depend on executing arbitrary code from scanned repositories.
- External network integration tests should be opt-in.
- Golden report tests must tolerate timestamps and stable generated IDs through normalization.
- Unit tests should use fixture repositories when possible.

