# tasks.md - GitHub Release Note Intelligence Agent

## Task T-001 - Confirm Project Planning Baseline

**Requirement mapping:** SPEC Sections 1-3, PLAN Sections 1-4  
**Type:** Foundation  
**Status:** Done

### Steps

- [x] Pull public repository.
- [x] Add knowledge-base documents.
- [x] Review `knowldege-base/SPEC.md` for product scope, requirements, runtime modes, and quality gates.
- [x] Review `knowldege-base/PLAN.md` for delivery phases, repository structure, and planning principles.
- [x] Create folder-only project skeleton.
- [x] Add module-level `specs.md` files.
- [x] Add report style specification.

### Acceptance Criteria

- [x] Repository has module boundaries.
- [x] Each module has an intent and input/output contract.
- [x] Report styling has a written design contract.
- [x] Planning baseline follows SPEC -> PLAN -> Tasks -> Code workflow.

## Task T-002 - Create Python Project Foundation

**Requirement mapping:** FR-014, FR-015, NFR-004  
**Type:** Foundation  
**Status:** Done

### Steps

- [x] Add `pyproject.toml`.
- [x] Add package initialization files.
- [x] Add application config module.
- [x] Add structured logging module.
- [x] Add minimal README with development commands.
- [x] Add `.env.example`.

### Acceptance Criteria

- [x] Package imports as `grna`.
- [x] Project can install in editable mode.
- [x] Basic lint/test commands are documented.

## Task T-003 - Define Core Data Models

**Requirement mapping:** FR-001, FR-002, FR-013, NFR-005  
**Type:** Foundation  
**Status:** Not Started

### Steps

- [ ] Define scan request model.
- [ ] Define job status model.
- [ ] Define repository metadata model.
- [ ] Define evidence item model.
- [ ] Define analyzer result model.
- [ ] Define analytics bundle model.
- [ ] Define artifact metadata model.
- [ ] Add unit tests for model validation.

### Acceptance Criteria

- [ ] Models support REST, MCP, CLI, and worker usage.
- [ ] Evidence model can reference files, commits, reports, and generated artifacts.
- [ ] Invalid request shapes fail with clear validation errors.

## Task T-004 - Implement Local Storage and Artifact Store

**Requirement mapping:** FR-021, NFR-005  
**Type:** Foundation  
**Status:** Done

### Steps

- [x] Implement local in-memory or JSON-backed job store for MVP.
- [x] Implement root-bound artifact path helper.
- [x] Implement artifact metadata creation.
- [x] Implement checksum generation.
- [x] Add unit tests for path safety.

### Acceptance Criteria

- [x] Artifacts cannot be written outside configured artifact root.
- [x] Job status can be saved and retrieved locally.
- [x] Artifact metadata includes path, type, timestamp, and checksum.

## Task T-005 - Implement Job State Machine

**Requirement mapping:** FR-001, NFR-001  
**Type:** Foundation  
**Status:** Done

### Steps

- [x] Define job states and valid transitions.
- [x] Implement job orchestrator skeleton.
- [x] Implement progress and stage update helpers.
- [x] Implement failure handling.
- [x] Add unit tests for valid and invalid transitions.

### Acceptance Criteria

- [x] Jobs move through explicit states.
- [x] Invalid transitions are rejected or logged.
- [x] Failures preserve error code and message.

## Task T-006 - Implement GitHub URL Validation

**Requirement mapping:** FR-001, FR-002, NFR-002  
**Type:** Repository Fetching  
**Status:** Done

### Steps

- [x] Validate supported GitHub URL formats.
- [x] Reject local paths and unsupported schemes.
- [x] Normalize owner/repo identity.
- [x] Redact credentials if present.
- [x] Add unit tests for valid and invalid URLs.

### Acceptance Criteria

- [x] Valid public GitHub URLs are accepted.
- [x] Invalid URLs return stable validation errors.
- [x] Local filesystem paths are rejected.

## Task T-007 - Implement Repository Fetcher

**Requirement mapping:** FR-002, NFR-002  
**Type:** Repository Fetching  
**Status:** Done

### Steps

- [x] Clone public repository into job workspace.
- [x] Resolve branch, tag, or commit SHA.
- [x] Capture resolved commit SHA and default branch.
- [x] Enforce workspace isolation.
- [x] Skip execution of repository code and hooks.
- [x] Add integration test with a small public repo or local fixture.

### Acceptance Criteria

- [x] Repository content exists under job-specific workspace.
- [x] Fetch metadata is recorded.
- [x] Fetch failures produce structured errors.

## Task T-008 - Implement Repository Inventory Analyzer

**Requirement mapping:** FR-003, FR-007, FR-011  
**Type:** Analyzer  
**Status:** Done

### Steps

- [x] Walk repository tree.
- [x] Skip `.git`, virtual environments, `node_modules`, build outputs, and caches.
- [x] Classify source, test, docs, config, CI, deployment, coverage, and binary files.
- [x] Produce file counts and size summary.
- [x] Add fixture-based tests.

### Acceptance Criteria

- [x] Inventory is deterministic.
- [x] Important files such as README, SPEC, HLD, LLD, Dockerfile, Helm, and coverage reports are detected.
- [x] Large/generated folders are skipped.

## Task T-009 - Implement Evidence Indexer

**Requirement mapping:** FR-011, NFR-005  
**Type:** Evidence  
**Status:** Done

### Steps

- [x] Create evidence IDs for important files and facts.
- [x] Store source path, source type, hash, and summary.
- [x] Add redaction hooks for sensitive values.
- [x] Link analyzer findings to evidence.
- [x] Add unit tests for deterministic IDs and redaction.

### Acceptance Criteria

- [x] Evidence records are generated for repository files and commits.
- [x] Evidence can be looked up by ID.
- [x] Sensitive values are not emitted to report-ready evidence.

## Task T-010 - Implement Technology Analyzer

**Requirement mapping:** FR-003  
**Type:** Analyzer  
**Status:** Done

### Steps

- [x] Detect languages from file extensions.
- [x] Detect Python packaging from `pyproject.toml` and `requirements.txt`.
- [x] Detect FastAPI, MCP, Pydantic, pytest, Ruff, Docker, Helm, Kubernetes, and GitHub Actions.
- [x] Assign confidence and evidence references.
- [x] Add unit tests with fixture manifests.

### Acceptance Criteria

- [x] Technology inventory includes evidence paths.
- [x] Unknown technologies are reported as unknown.
- [x] Confidence is present for each finding.

## Task T-011 - Implement Spec and Documentation Analyzer

**Requirement mapping:** FR-004, FR-011  
**Type:** Analyzer  
**Status:** Done

### Steps

- [x] Detect README, SPEC, HLD, LLD, docs, ADRs, and module-level specs.
- [x] Extract headings and concise summaries.
- [x] Identify project intent from documentation.
- [x] Record documentation gaps.
- [x] Add tests with fixture docs.

### Acceptance Criteria

- [x] Documentation inventory is produced.
- [x] Project intent distinguishes stated and inferred evidence.
- [x] Missing specs are listed as gaps.

## Task T-012 - Implement Commit Analyzer

**Requirement mapping:** FR-008  
**Type:** Analyzer  
**Status:** Done

### Steps

- [x] Read commit history from selected range.
- [x] Collect authors, dates, changed files, and tags.
- [x] Categorize conventional commits and heuristic categories.
- [x] Identify hotspots and risky changed areas.
- [x] Add tests against fixture Git repository.

### Acceptance Criteria

- [x] Commit count, authors, date range, and changed files are reported.
- [x] Uncategorized commits remain explicit.
- [x] Analyzer does not fabricate change categories.

## Task T-013 - Implement Code Structure Analyzer

**Requirement mapping:** FR-007  
**Type:** Analyzer  
**Status:** Done

### Steps

- [x] Build directory and module summary.
- [x] Parse Python files with `ast`.
- [x] Identify entrypoints, classes, functions, imports, and public surfaces.
- [x] Estimate lines of code by module.
- [x] Add tests with Python fixture modules.

### Acceptance Criteria

- [x] Module inventory is generated.
- [x] Entrypoints are identified when evidence exists.
- [x] Unsupported languages produce partial-analysis gaps.

## Task T-014 - Implement Interface Analyzer

**Requirement mapping:** FR-006  
**Type:** Analyzer  
**Status:** Done

### Steps

- [x] Detect FastAPI route decorators.
- [x] Detect CLI command patterns.
- [x] Detect MCP tool definitions.
- [x] Detect environment variables and config files.
- [x] Detect generated artifact paths.
- [x] Add tests for route and CLI fixtures.

### Acceptance Criteria

- [x] Interface inventory includes type, direction, evidence, and confidence.
- [x] Missing explicit contracts are listed as recommendations.
- [x] Analyzer remains read-only.

## Task T-015 - Implement Test and Coverage Analyzers

**Requirement mapping:** FR-009, FR-010  
**Type:** Analyzer  
**Status:** Done

### Steps

- [x] Detect test source files.
- [x] Detect pytest/JUnit test reports.
- [x] Parse `coverage.xml`.
- [x] Parse `lcov.info`.
- [x] Parse JaCoCo XML where practical.
- [x] Report unavailable evidence clearly.

### Acceptance Criteria

- [x] Test file inventory is produced.
- [x] Coverage is reported only when evidence exists.
- [x] Missing test/coverage evidence is explicit.

## Task T-016 - Implement Analytics Aggregator

**Requirement mapping:** FR-013, NFR-005  
**Type:** Evidence  
**Status:** Done

### Steps

- [x] Combine analyzer outputs into analytics bundle.
- [x] Normalize warnings and known gaps.
- [x] Attach evidence references.
- [x] Add JSON serialization.
- [x] Add unit tests.

### Acceptance Criteria

- [x] A single analytics JSON object can drive report generation.
- [x] All major sections have evidence or explicit gaps.

## Task T-017 - Implement Mermaid Diagram Generator

**Requirement mapping:** FR-012  
**Type:** Report Generation  
**Status:** Done

### Steps

- [x] Generate repository analysis flow diagram.
- [x] Generate C4 context diagram.
- [x] Generate C4 container diagram.
- [x] Generate component diagram.
- [x] Generate deployment topology when evidence exists.
- [x] Add snapshot tests for Mermaid output.

### Acceptance Criteria

- [x] Diagram source is valid Mermaid-compatible text.
- [x] Diagrams include captions and confidence.
- [x] Missing evidence is handled gracefully.

## Task T-018 - Implement Markdown Release Note Generator

**Requirement mapping:** FR-013  
**Type:** Report Generation  
**Status:** Done

### Steps

- [x] Create report content model.
- [x] Create Markdown template.
- [x] Render required sections.
- [x] Include Mermaid diagram blocks.
- [x] Include evidence appendix.
- [x] Add golden-file tests.

### Acceptance Criteria

- [x] Markdown report is generated for successful scan.
- [x] Required sections are present.
- [x] Missing evidence statements are present.

## Task T-019 - Implement HTML Report Theme

**Requirement mapping:** FR-013, `docs/report-style-spec.md`  
**Type:** Report Generation  
**Status:** Done

### Steps

- [x] Create HTML template.
- [x] Implement theme tokens.
- [x] Implement cover/dashboard layout.
- [x] Implement page-like sections for print.
- [x] Implement tables, metric tiles, callouts, and evidence blocks.
- [x] Add visual smoke test.

### Acceptance Criteria

- [x] HTML follows `docs/report-style-spec.md`.
- [x] HTML is readable without external network assets.
- [x] HTML can be used as PDF source.

## Task T-020 - Implement PDF Renderer

**Requirement mapping:** FR-013, `docs/report-style-spec.md`  
**Type:** Report Generation  
**Status:** Done

### Steps

- [x] Select initial PDF renderer.
- [x] Render HTML to PDF.
- [x] Preserve cover page, headers, page numbers, tables, and diagrams/source.
- [x] Add fallback behavior when PDF render fails.
- [x] Compare output against reference PDF style.

### Acceptance Criteria

- [x] PDF artifact is generated when requested.
- [x] Markdown and HTML are preserved if PDF generation fails.
- [x] PDF visual style is recognizably aligned with the reference sample.

## Task T-021 - Implement REST API MVP

**Requirement mapping:** FR-014  
**Type:** API  
**Status:** Done

### Steps

- [x] Add FastAPI app factory.
- [x] Add health and readiness endpoints.
- [x] Add scan creation endpoint.
- [x] Add job status endpoint.
- [x] Add analytics endpoint.
- [x] Add artifact listing and download endpoints.
- [x] Add API contract tests.

### Acceptance Criteria

- [x] API starts locally.
- [x] Valid scan request creates a job.
- [x] Job status and artifacts can be queried.

## Task T-022 - Implement CLI MVP

**Requirement mapping:** LLD Runtime Modes  
**Type:** CLI  
**Status:** Done

### Steps

- [x] Add `scan` command.
- [x] Add `status` command.
- [x] Add `generate-note` command for local analytics input.
- [x] Add JSON output option.
- [x] Add CLI tests.

### Acceptance Criteria

- [x] CLI can run a local end-to-end MVP scan.
- [x] CLI returns useful errors.

## Task T-023 - Implement MCP Server MVP

**Requirement mapping:** FR-015  
**Type:** MCP  
**Status:** Done

### Steps

- [x] Add MCP server entrypoint.
- [x] Add scan start tool.
- [x] Add scan status tool.
- [x] Add analytics retrieval tool.
- [x] Add artifact retrieval tool.
- [x] Add MCP schema tests.

### Acceptance Criteria

- [x] MCP tools delegate to shared service layer.
- [x] MCP tool responses are structured and deterministic.

## Task T-024 - Build End-to-End MVP Flow

**Requirement mapping:** Definition of Done items 1-12  
**Type:** Integration  
**Status:** Done

### Steps

- [x] Wire fetcher, inventory, evidence, analyzers, diagrams, and report generation.
- [x] Run against `https://github.com/aveeshek/bosgenesis-mop-creation-agent`.
- [x] Generate Markdown, HTML, and PDF artifacts.
- [x] Review report for evidence accuracy.
- [x] Capture known gaps.

### Acceptance Criteria

- [x] Given a GitHub URL, agent generates a human-readable release note.
- [x] Report follows the reference style contract.
- [x] Claims include evidence references or explicit gaps.

## Task T-025 - Add Security and Safety Hardening

**Requirement mapping:** NFR-002, Security Specification  
**Type:** Hardening  
**Status:** Not Started

### Steps

- [ ] Enforce max repository size.
- [ ] Enforce max file size.
- [ ] Redact secret-like values.
- [ ] Prevent artifact path traversal.
- [ ] Ensure scanned repo code is not executed.
- [ ] Add negative tests.

### Acceptance Criteria

- [ ] Security controls are tested.
- [ ] Generated reports do not include raw secrets.
- [ ] Unsafe paths and URLs are rejected.

## Task T-026 - Add Observability

**Requirement mapping:** NFR-004  
**Type:** Hardening  
**Status:** Done

### Steps

- [x] Add structured job-stage logs.
- [x] Add analyzer duration metrics hooks.
- [x] Add artifact generation events.
- [x] Add audit events for job creation and artifact download.
- [x] Add tests for log/event shapes where practical.

### Acceptance Criteria

- [x] Each major stage emits start/completion/failure logs.
- [x] Logs include `job_id`, `stage`, `event`, and `status`.

## Task T-027 - Add Docker and Local Runtime Support

**Requirement mapping:** Phase 5 Production Hardening  
**Type:** Deployment  
**Status:** Done

### Steps

- [x] Add Dockerfile.
- [x] Docker Compose intentionally excluded by project decision; use Dockerfile
  for local API runtime and Helm/Kubernetes for deployment.
- [x] Document local run commands.
- [x] Add container smoke test.

### Acceptance Criteria

- [x] API can run in container locally.
- [x] Artifact and workspace paths are configurable.

## Task T-028 - Add Helm Chart Skeleton

**Requirement mapping:** Phase 5 Production Hardening  
**Type:** Deployment  
**Status:** Done

### Steps

- [x] Add `Chart.yaml`.
- [x] Add values file.
- [x] Add API deployment/service templates.
- [x] Add MCP deployment/service templates.
- [x] Add worker deployment template.
- [x] Add artifact PVC template.

### Acceptance Criteria

- [x] Helm template renders without errors.
- [x] Secret values are referenced, not embedded.

## Task T-029 - Acceptance Test Suite

**Requirement mapping:** Acceptance Test Scenarios  
**Type:** Testing  
**Status:** Not Started

### Steps

- [ ] Test valid public repo scan.
- [ ] Test missing coverage behavior.
- [ ] Test repository with specs behavior.
- [ ] Test REST scan workflow.
- [ ] Test MCP scan workflow.
- [ ] Test PDF generation workflow.

### Acceptance Criteria

- [ ] MVP acceptance scenarios pass.
- [ ] Failure cases produce user-readable errors.
