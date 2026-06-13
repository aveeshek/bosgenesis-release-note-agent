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
**Status:** Not Started

### Steps

- [ ] Detect languages from file extensions.
- [ ] Detect Python packaging from `pyproject.toml` and `requirements.txt`.
- [ ] Detect FastAPI, MCP, Pydantic, pytest, Ruff, Docker, Helm, Kubernetes, and GitHub Actions.
- [ ] Assign confidence and evidence references.
- [ ] Add unit tests with fixture manifests.

### Acceptance Criteria

- [ ] Technology inventory includes evidence paths.
- [ ] Unknown technologies are reported as unknown.
- [ ] Confidence is present for each finding.

## Task T-011 - Implement Spec and Documentation Analyzer

**Requirement mapping:** FR-004, FR-011  
**Type:** Analyzer  
**Status:** Not Started

### Steps

- [ ] Detect README, SPEC, HLD, LLD, docs, ADRs, and module-level specs.
- [ ] Extract headings and concise summaries.
- [ ] Identify project intent from documentation.
- [ ] Record documentation gaps.
- [ ] Add tests with fixture docs.

### Acceptance Criteria

- [ ] Documentation inventory is produced.
- [ ] Project intent distinguishes stated and inferred evidence.
- [ ] Missing specs are listed as gaps.

## Task T-012 - Implement Commit Analyzer

**Requirement mapping:** FR-008  
**Type:** Analyzer  
**Status:** Not Started

### Steps

- [ ] Read commit history from selected range.
- [ ] Collect authors, dates, changed files, and tags.
- [ ] Categorize conventional commits and heuristic categories.
- [ ] Identify hotspots and risky changed areas.
- [ ] Add tests against fixture Git repository.

### Acceptance Criteria

- [ ] Commit count, authors, date range, and changed files are reported.
- [ ] Uncategorized commits remain explicit.
- [ ] Analyzer does not fabricate change categories.

## Task T-013 - Implement Code Structure Analyzer

**Requirement mapping:** FR-007  
**Type:** Analyzer  
**Status:** Not Started

### Steps

- [ ] Build directory and module summary.
- [ ] Parse Python files with `ast`.
- [ ] Identify entrypoints, classes, functions, imports, and public surfaces.
- [ ] Estimate lines of code by module.
- [ ] Add tests with Python fixture modules.

### Acceptance Criteria

- [ ] Module inventory is generated.
- [ ] Entrypoints are identified when evidence exists.
- [ ] Unsupported languages produce partial-analysis gaps.

## Task T-014 - Implement Interface Analyzer

**Requirement mapping:** FR-006  
**Type:** Analyzer  
**Status:** Not Started

### Steps

- [ ] Detect FastAPI route decorators.
- [ ] Detect CLI command patterns.
- [ ] Detect MCP tool definitions.
- [ ] Detect environment variables and config files.
- [ ] Detect generated artifact paths.
- [ ] Add tests for route and CLI fixtures.

### Acceptance Criteria

- [ ] Interface inventory includes type, direction, evidence, and confidence.
- [ ] Missing explicit contracts are listed as recommendations.
- [ ] Analyzer remains read-only.

## Task T-015 - Implement Test and Coverage Analyzers

**Requirement mapping:** FR-009, FR-010  
**Type:** Analyzer  
**Status:** Not Started

### Steps

- [ ] Detect test source files.
- [ ] Detect pytest/JUnit test reports.
- [ ] Parse `coverage.xml`.
- [ ] Parse `lcov.info`.
- [ ] Parse JaCoCo XML where practical.
- [ ] Report unavailable evidence clearly.

### Acceptance Criteria

- [ ] Test file inventory is produced.
- [ ] Coverage is reported only when evidence exists.
- [ ] Missing test/coverage evidence is explicit.

## Task T-016 - Implement Analytics Aggregator

**Requirement mapping:** FR-013, NFR-005  
**Type:** Evidence  
**Status:** Not Started

### Steps

- [ ] Combine analyzer outputs into analytics bundle.
- [ ] Normalize warnings and known gaps.
- [ ] Attach evidence references.
- [ ] Add JSON serialization.
- [ ] Add unit tests.

### Acceptance Criteria

- [ ] A single analytics JSON object can drive report generation.
- [ ] All major sections have evidence or explicit gaps.

## Task T-017 - Implement Mermaid Diagram Generator

**Requirement mapping:** FR-012  
**Type:** Report Generation  
**Status:** Not Started

### Steps

- [ ] Generate repository analysis flow diagram.
- [ ] Generate C4 context diagram.
- [ ] Generate C4 container diagram.
- [ ] Generate component diagram.
- [ ] Generate deployment topology when evidence exists.
- [ ] Add snapshot tests for Mermaid output.

### Acceptance Criteria

- [ ] Diagram source is valid Mermaid-compatible text.
- [ ] Diagrams include captions and confidence.
- [ ] Missing evidence is handled gracefully.

## Task T-018 - Implement Markdown Release Note Generator

**Requirement mapping:** FR-013  
**Type:** Report Generation  
**Status:** Not Started

### Steps

- [ ] Create report content model.
- [ ] Create Markdown template.
- [ ] Render required sections.
- [ ] Include Mermaid diagram blocks.
- [ ] Include evidence appendix.
- [ ] Add golden-file tests.

### Acceptance Criteria

- [ ] Markdown report is generated for successful scan.
- [ ] Required sections are present.
- [ ] Missing evidence statements are present.

## Task T-019 - Implement HTML Report Theme

**Requirement mapping:** FR-013, `docs/report-style-spec.md`  
**Type:** Report Generation  
**Status:** Not Started

### Steps

- [ ] Create HTML template.
- [ ] Implement theme tokens.
- [ ] Implement cover/dashboard layout.
- [ ] Implement page-like sections for print.
- [ ] Implement tables, metric tiles, callouts, and evidence blocks.
- [ ] Add visual smoke test.

### Acceptance Criteria

- [ ] HTML follows `docs/report-style-spec.md`.
- [ ] HTML is readable without external network assets.
- [ ] HTML can be used as PDF source.

## Task T-020 - Implement PDF Renderer

**Requirement mapping:** FR-013, `docs/report-style-spec.md`  
**Type:** Report Generation  
**Status:** Not Started

### Steps

- [ ] Select initial PDF renderer.
- [ ] Render HTML to PDF.
- [ ] Preserve cover page, headers, page numbers, tables, and diagrams/source.
- [ ] Add fallback behavior when PDF render fails.
- [ ] Compare output against reference PDF style.

### Acceptance Criteria

- [ ] PDF artifact is generated when requested.
- [ ] Markdown and HTML are preserved if PDF generation fails.
- [ ] PDF visual style is recognizably aligned with the reference sample.

## Task T-021 - Implement REST API MVP

**Requirement mapping:** FR-014  
**Type:** API  
**Status:** Not Started

### Steps

- [ ] Add FastAPI app factory.
- [ ] Add health and readiness endpoints.
- [ ] Add scan creation endpoint.
- [ ] Add job status endpoint.
- [ ] Add analytics endpoint.
- [ ] Add artifact listing and download endpoints.
- [ ] Add API contract tests.

### Acceptance Criteria

- [ ] API starts locally.
- [ ] Valid scan request creates a job.
- [ ] Job status and artifacts can be queried.

## Task T-022 - Implement CLI MVP

**Requirement mapping:** LLD Runtime Modes  
**Type:** CLI  
**Status:** Not Started

### Steps

- [ ] Add `scan` command.
- [ ] Add `status` command.
- [ ] Add `generate-note` command for local analytics input.
- [ ] Add JSON output option.
- [ ] Add CLI tests.

### Acceptance Criteria

- [ ] CLI can run a local end-to-end MVP scan.
- [ ] CLI returns useful errors.

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
**Status:** Not Started

### Steps

- [ ] Wire fetcher, inventory, evidence, analyzers, diagrams, and report generation.
- [ ] Run against `https://github.com/aveeshek/bosgenesis-mop-creation-agent`.
- [ ] Generate Markdown, HTML, and PDF artifacts.
- [ ] Review report for evidence accuracy.
- [ ] Capture known gaps.

### Acceptance Criteria

- [ ] Given a GitHub URL, agent generates a human-readable release note.
- [ ] Report follows the reference style contract.
- [ ] Claims include evidence references or explicit gaps.

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
**Status:** Not Started

### Steps

- [ ] Add structured job-stage logs.
- [ ] Add analyzer duration metrics hooks.
- [ ] Add artifact generation events.
- [ ] Add audit events for job creation and artifact download.
- [ ] Add tests for log/event shapes where practical.

### Acceptance Criteria

- [ ] Each major stage emits start/completion/failure logs.
- [ ] Logs include `job_id`, `stage`, `event`, and `status`.

## Task T-027 - Add Docker and Local Runtime Support

**Requirement mapping:** Phase 5 Production Hardening  
**Type:** Deployment  
**Status:** Not Started

### Steps

- [ ] Add Dockerfile.
- [ ] Add docker-compose for API, worker, Redis, and optional PostgreSQL.
- [ ] Document local run commands.
- [ ] Add container smoke test.

### Acceptance Criteria

- [ ] API can run in container locally.
- [ ] Artifact and workspace paths are configurable.

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
