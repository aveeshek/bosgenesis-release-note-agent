# Runtime Module Specification

## Intent

Provide shared runtime services used by CLI, REST API, MCP, and future workers.
The runtime module owns the end-to-end repository scan pipeline so every entry
point produces consistent job state, analytics, evidence, diagrams, and report
artifacts.

## Role

- Fetch public GitHub repositories or explicit local test fixtures.
- Run inventory, evidence, technology, documentation, commit, code structure,
  interface, test/coverage, and release-readiness analyzers.
- Aggregate analyzer outputs, including evidence-driven readiness scoring, into
  one analytics bundle.
- Generate Mermaid diagrams and Markdown/HTML/PDF release-note artifacts.
- Persist jobs and artifacts through injected storage interfaces.

## Inputs

- `ScanPipelineRequest` with repository URL, optional ref, release name, output
  formats, runtime label, optional existing `job_id`, and optional test fixture
  path.
- Runtime configuration for workspace, job, and artifact roots.
- Job and artifact storage adapters.
- Local analytics/evidence JSON files for report-only rendering.

## Outputs

- Completed or failed job records.
- Analytics, evidence, fetch metadata, Markdown, HTML, and optional PDF artifacts.
- Structured response payloads suitable for CLI, REST, and MCP.
- Stable error codes and useful messages on failure.

## Design Rules

- The pipeline must remain read-only with respect to scanned repository code.
- Public repository scans must use GitHub URL validation and isolated workspaces.
- Runtime functions must support dependency injection for tests and future
  PostgreSQL-backed stores.
- Runtime scans may attach to an already-created queued job so MCP submission can
  return immediately and let a background worker update the same job record.
- Missing evidence must be represented as gaps, not hidden.
- PDF rendering should prefer styled HTML as the source and preserve Markdown/HTML
  artifacts if PDF generation fails.
