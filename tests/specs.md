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
- Repository inventory classification, important file detection, and generated-folder skip rules.
- Analyzer contracts and evidence references.
- Technology detection from extensions, Python manifests, deployment assets, CI files, and unknown-language repositories.
- Documentation detection for README, SPEC, HLD, LLD, docs, ADRs, module specs, intent extraction, and gaps.
- Commit history analysis with fixture Git repositories, selected ranges, tags, authors, changed files, categories, and hotspots.
- Python code structure analysis with AST fixtures, entrypoints, public surfaces, LOC, and unsupported-language gaps.
- Interface analysis for FastAPI routes, CLI commands, MCP tools, environment variables, config files, artifacts, and recommendations.
- Test and coverage report parsing for source files, pytest/JUnit XML, coverage.xml, lcov.info, JaCoCo XML, and missing evidence.
- Analytics aggregation for section normalization, JSON serialization, gaps, warnings, and evidence ID collection.
- Mermaid diagram snapshot tests for repository flow, C4-style diagrams, deployment topology, metadata, and missing evidence.
- Markdown report golden-style tests for required sections, Mermaid fences, missing evidence statements, and evidence appendix.
- HTML report smoke tests for inline theme tokens, cover/dashboard layout, print CSS, tables, callouts, Mermaid source, and evidence blocks.
- PDF report tests for successful PDF bytes when the renderer is available and structured preservation metadata when rendering fails.
- REST API contract tests for health/readiness, scan creation, job status, analytics placeholders, artifact metadata, artifact download, invalid URLs, and missing jobs.
- CLI contract tests for local fixture scan, status lookup, analytics-driven `generate-note`, JSON output, and useful structured errors.
- End-to-end MVP validation should run the CLI scan flow against the BOS Genesis MoP Creation Agent repository input and verify Markdown, HTML, PDF, analytics, evidence, and explicit gaps.
- Deterministic evidence IDs, evidence lookup, commit/fact records, and redaction.
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
