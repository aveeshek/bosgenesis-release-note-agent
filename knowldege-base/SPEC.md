# SPEC.md — GitHub Release Note Intelligence Agent

**Document Version:** 1.0  
**Target System:** GitHub Release Note Intelligence Agent  
**Primary Language:** Python  
**Runtime Modes:** REST API, MCP Server, CLI Worker  
**Document Type:** Product + Engineering Specification for Spec-Driven Development  
**Status:** Draft for Implementation Planning  

---

## 1. Purpose

This specification defines the expected behavior, interfaces, quality gates, data contracts, and acceptance criteria for a Python-based agent that scans public GitHub repositories, understands the codebase, analyzes project evidence, and generates a professional industry-standard release note package.

The agent must also operate as an MCP server so external orchestrators such as Codex-style tools, Kiro CLI, Claude Code, BOS Genesis agents, n8n workflows, or other MCP-compatible clients can invoke repository scanning, analytics, and release-note generation capabilities through governed tools.

---

## 2. Product Vision

The GitHub Release Note Intelligence Agent will convert a raw GitHub repository into a polished release intelligence package.

The generated release package should include:

- Executive release summary
- Project intent and capability analysis
- Technology and tooling inventory
- Feature inventory
- Input/output contract analysis
- API/interface analytics
- Commit history analytics
- Test and coverage analytics
- Code quality and module analytics
- Architecture diagrams
- Mermaid flow diagrams
- C4 context/container/component diagrams
- Deployment diagrams
- Risk, known gaps, and change impact sections
- Professional Markdown, HTML, and PDF output

The output should resemble a commercial-grade release note or technical delivery report, not a plain changelog.

---

## 3. Scope

### 3.1 In Scope

The agent must support the following capabilities:

1. Scan a public GitHub repository.
2. Clone or fetch repository content safely into an isolated workspace.
3. Detect project language, framework, tools, packaging system, and runtime model.
4. Infer project intent from README files, code structure, configuration, documentation, and commit history.
5. Identify project features and major functional areas.
6. Identify input and output contracts such as REST APIs, CLI commands, message formats, config files, environment variables, MCP tools, workflow payloads, and generated artifacts.
7. Analyze source code by directory and module.
8. Read commit history and produce change analytics.
9. Read coverage data if available.
10. Read unit test results if available.
11. Read HLD, LLD, `SPEC.md`, and nested directory-level spec files if available.
12. Generate evidence-backed release notes.
13. Generate Mermaid diagrams.
14. Generate C4-style diagrams.
15. Generate deployment topology diagrams.
16. Generate professional Markdown and HTML output.
17. Generate professional PDF output.
18. Expose all major actions as REST APIs.
19. Expose all major actions as MCP tools.
20. Run long scans asynchronously.
21. Persist job state, evidence, analytics, and generated output.
22. Provide traceability between release-note claims and source evidence.

### 3.2 Out of Scope for MVP

The MVP does not need to support:

1. Private GitHub repository access.
2. GitHub Enterprise authentication.
3. Writing back to the repository.
4. Creating GitHub releases automatically.
5. Opening pull requests automatically.
6. Running arbitrary untrusted repository code.
7. Full static application security testing.
8. Full license legal review.
9. Full SBOM generation.
10. Production multi-tenant billing or user management.

These items may be added in later phases.

---

## 4. Stakeholders

| Stakeholder | Need |
|---|---|
| Engineering Lead | Understand what changed and whether the release is ready |
| Architect | Understand architecture, interfaces, and deployment impact |
| QA Lead | Understand test coverage, unit tests, and quality signals |
| Release Manager | Generate a professional release note package |
| Developer | Validate feature, module, and commit interpretation |
| MCP Client / Agent | Invoke scan and release-note generation as tools |
| Executive Reader | Read a polished summary without reviewing code |

---

## 5. User Personas

### 5.1 Platform Engineer

Wants to generate a professional release document from a GitHub repository without manually reading every file.

### 5.2 Software Architect

Wants architecture diagrams, component relationships, interface inventory, and deployment implications.

### 5.3 QA / Test Lead

Wants coverage, unit test evidence, test gaps, and release confidence indicators.

### 5.4 Release Manager

Wants a polished release note that can be shared with stakeholders.

### 5.5 Autonomous Agent / MCP Client

Wants to call repository analysis and document generation tools programmatically.

---

## 6. Primary User Journey

1. User submits a public GitHub repository URL.
2. Agent creates an asynchronous scan job.
3. Agent clones or fetches repository content.
4. Agent scans project structure.
5. Agent identifies technologies and tools.
6. Agent reads README, HLD, LLD, specs, and documentation.
7. Agent analyzes source modules.
8. Agent analyzes interfaces and contracts.
9. Agent reads commit history.
10. Agent reads coverage and unit test files if present.
11. Agent generates analytics and evidence objects.
12. Agent generates diagrams.
13. Agent generates a professional release note in Markdown.
14. Agent renders HTML and PDF.
15. User downloads the release package.
16. MCP clients can retrieve the same artifacts using tool calls.

---

## 7. Functional Requirements

### FR-001 — Repository Scan Job Creation

The system shall accept a public GitHub repository URL and create an asynchronous scan job.

**Inputs:**

- `repo_url`
- optional `branch`
- optional `tag`
- optional `commit_sha`
- optional `release_name`
- optional `output_formats`
- optional `analysis_depth`

**Outputs:**

- `job_id`
- `status`
- `created_at`
- `status_url`

**Acceptance Criteria:**

- Given a valid public GitHub URL, the system returns a job ID.
- Given an invalid URL, the system returns a validation error.
- Given both branch and tag, the system applies deterministic precedence or rejects the request with a clear error.
- Job creation must complete quickly and not block on full repository scanning.

---

### FR-002 — Repository Fetching

The system shall fetch repository content into an isolated local workspace.

**Acceptance Criteria:**

- Repository content is stored under a job-specific workspace.
- Existing workspaces are not reused across jobs unless caching is explicitly enabled.
- The system records fetch metadata: remote URL, branch, tag, commit SHA, fetch timestamp.
- The system must not execute repository code during fetch.

---

### FR-003 — Project Technology Detection

The system shall detect project languages, frameworks, tools, and runtime model.

**Signals:**

- File extensions
- Dependency manifests
- Dockerfiles
- Helm charts
- Kubernetes YAML
- CI/CD files
- README content
- Import patterns
- Package metadata

**Examples:**

| Evidence | Technology Inference |
|---|---|
| `pyproject.toml`, `requirements.txt` | Python project |
| `package.json` | Node.js / frontend project |
| `pom.xml` | Maven / Java project |
| `Dockerfile` | Containerized application |
| `Chart.yaml` | Helm deployment |
| `server.py`, `FastAPI` import | FastAPI service |
| `mcp.server` imports | MCP server capability |

**Acceptance Criteria:**

- The agent returns a technology inventory with confidence score.
- Each technology claim has evidence references.
- Unknown technologies are reported as unknown, not guessed with high confidence.

---

### FR-004 — Project Intent Analysis

The system shall infer the intent of the project.

**Input Sources:**

- README files
- HLD / LLD documents
- SPEC.md
- Source code entrypoints
- API route names
- CLI commands
- Commit messages
- Test names

**Output:**

- `project_intent_summary`
- `business_capability_summary`
- `technical_capability_summary`
- confidence score
- evidence references

**Acceptance Criteria:**

- The project intent summary must be concise and evidence-backed.
- The agent must distinguish between stated intent and inferred intent.
- If documentation is missing, the agent must say that intent is inferred from code and commit evidence.

---

### FR-005 — Feature Discovery

The system shall identify project features and group them by capability area.

**Output Example:**

```yaml
features:
  - name: Repository scanner
    category: ingestion
    evidence:
      - src/scanner/github_scanner.py
      - README.md
    confidence: high
  - name: PDF release note rendering
    category: document_generation
    evidence:
      - src/renderers/pdf_renderer.py
    confidence: medium
```

**Acceptance Criteria:**

- Features are grouped by category.
- Features include evidence references.
- Feature confidence is shown.
- The system separates implemented features from planned features when possible.

---

### FR-006 — Input and Output Contract Analysis

The system shall identify project contracts.

**Contract Types:**

- REST API endpoints
- MCP tools
- CLI commands
- Environment variables
- Config files
- Request/response schemas
- Message topics
- File input/output formats
- Database tables
- Generated artifacts

**Acceptance Criteria:**

- The release note includes an interface inventory.
- Each interface includes direction: input, output, or bidirectional.
- Each interface includes consumer/provider when inferable.
- Each interface includes evidence references.

---

### FR-007 — Source Code Analysis

The system shall scan source code and produce module-level analytics.

**Metrics:**

- Number of source files
- Lines of code
- Directory/module grouping
- Entry points
- Public functions/classes
- Complexity indicators if available
- Dependency graph if inferable
- Internal module relationships

**Acceptance Criteria:**

- The system produces a module inventory.
- The system identifies entrypoint modules.
- The system identifies high-change or high-complexity modules when enough evidence exists.

---

### FR-008 — Commit History Analysis

The system shall analyze Git commit history.

**Metrics:**

- Total commits in selected range
- Commits by author
- Commits by date
- Files changed frequently
- Change categories
- Bugfix versus feature versus refactor signals
- First and latest commit considered
- Tag-to-tag comparison when tags exist

**Acceptance Criteria:**

- Commit analysis supports full-history and range-based modes.
- The system must not invent commit categories without evidence.
- The system includes commit analytics in release note.

---

### FR-009 — Coverage Data Analysis

The system shall detect and parse coverage data when available.

**Supported Files for MVP:**

- `coverage.xml`
- `.coverage` when parseable
- `htmlcov/index.html` summary when parseable
- `lcov.info`
- `coverage-final.json`
- `jacoco.xml`

**Acceptance Criteria:**

- If coverage exists, report line coverage and file-level coverage when possible.
- If coverage does not exist, clearly mark coverage as unavailable.
- The system must not run tests by default to generate coverage.

---

### FR-010 — Unit Test Data Analysis

The system shall detect unit test files and test reports.

**Supported Evidence:**

- `tests/` folder
- `test_*.py`
- `*_test.py`
- `junit.xml`
- `pytest.xml`
- Surefire reports
- Jest reports
- GitHub Actions test artifacts if available in repository files

**Acceptance Criteria:**

- The system reports number of test files.
- The system reports parsed test results when reports exist.
- The system distinguishes test source files from executed test results.

---

### FR-011 — Specification Document Analysis

The system shall read specification documents.

**Document Types:**

- `README.md`
- `HLD.md`
- `LLD.md`
- `SPEC.md`
- `docs/**/*.md`
- module-level `SPEC.md`
- architecture decision records
- OpenAPI specs
- AsyncAPI specs

**Acceptance Criteria:**

- The system reports which specification documents exist.
- The system identifies gaps between specs and code when inferable.
- The release note references relevant specs.

---

### FR-012 — Diagram Generation

The system shall generate diagrams from discovered architecture evidence.

**Diagram Types:**

- Mermaid flow diagram
- Mermaid sequence diagram
- Mermaid component diagram
- C4 context diagram
- C4 container diagram
- C4 component diagram
- Deployment topology diagram
- Interface relationship diagram
- Data flow diagram
- Git/change timeline diagram when useful

**Acceptance Criteria:**

- Diagrams must be generated in Mermaid-compatible syntax where applicable.
- Diagrams must be included in Markdown output.
- Diagrams must be renderable in HTML/PDF output.
- If architecture evidence is weak, diagrams must be marked as inferred.

---

### FR-013 — Release Note Generation

The system shall generate a professional release note document.

**Minimum Sections:**

1. Cover / release identity
2. Executive summary
3. Release scope
4. Project intent
5. Technology inventory
6. Architecture overview
7. Feature summary
8. Interface inventory
9. Code analytics
10. Test and coverage analytics
11. Commit analytics
12. Deployment view
13. Risk and quality notes
14. Known gaps
15. Evidence and traceability
16. Appendix

**Acceptance Criteria:**

- Markdown release note is generated for every successful scan.
- PDF release note is generated when requested.
- The release note must clearly state missing evidence, not hide it.
- The release note must be professional and industry-standard in tone and layout.

---

### FR-014 — REST API Mode

The system shall expose REST APIs for scan and artifact retrieval.

**Required Endpoints:**

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/scans` | Create scan job |
| `GET` | `/api/v1/scans/{job_id}` | Get job status |
| `GET` | `/api/v1/scans/{job_id}/analytics` | Get analytics JSON |
| `GET` | `/api/v1/scans/{job_id}/release-note.md` | Download Markdown |
| `GET` | `/api/v1/scans/{job_id}/release-note.html` | Download HTML |
| `GET` | `/api/v1/scans/{job_id}/release-note.pdf` | Download PDF |
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check |

**Acceptance Criteria:**

- APIs return structured JSON errors.
- Long-running work is not performed inside request thread.
- Generated artifacts are retrievable by job ID.

---

### FR-015 — MCP Server Mode

The system shall expose MCP tools for agentic orchestration.

**Required MCP Tools:**

| Tool | Purpose |
|---|---|
| `github_release_scan_start` | Start repository scan |
| `github_release_scan_status` | Get scan status |
| `github_release_get_analytics` | Get analytics JSON |
| `github_release_generate_note` | Generate or regenerate release note |
| `github_release_get_artifact` | Retrieve generated artifact metadata/path |
| `github_release_list_evidence` | List evidence references |
| `github_release_get_diagrams` | Retrieve diagram definitions |

**Acceptance Criteria:**

- MCP tools use JSON-schema-defined inputs and outputs.
- MCP tool calls are safe and deterministic.
- MCP mode must not require REST API mode to be enabled, though both can run together.

---

## 8. Non-Functional Requirements

### NFR-001 — Asynchronous Execution

Repository analysis must run asynchronously.

**Acceptance Criteria:**

- Large repositories do not block HTTP or MCP request handlers.
- Job status can be queried during execution.
- Job stages are visible.

---

### NFR-002 — Security

The agent must safely process untrusted public repositories.

**Security Rules:**

- Do not execute repository code by default.
- Do not run install scripts by default.
- Do not expose secrets in generated reports.
- Redact tokens, passwords, private keys, and credentials from evidence.
- Use job-specific isolated workspaces.
- Enforce maximum repository size.
- Enforce maximum file size.
- Enforce allowed output directories.

---

### NFR-003 — Performance

The MVP should support small to medium repositories efficiently.

**Targets:**

| Metric | Target |
|---|---|
| Job creation latency | < 2 seconds |
| Small repo scan | < 2 minutes |
| Medium repo scan | < 10 minutes |
| Artifact retrieval | < 5 seconds |

---

### NFR-004 — Observability

The system must emit logs, metrics, and traces.

**Required Observability:**

- Structured logs
- Job stage logs
- Error details
- Scan duration metrics
- Analyzer duration metrics
- Artifact generation duration
- Optional OpenTelemetry tracing
- Optional Langfuse trace for LLM-based reasoning

---

### NFR-005 — Deterministic Evidence

Generated claims must be traceable.

**Acceptance Criteria:**

- Every major claim has evidence references.
- The release note distinguishes source evidence from LLM inference.
- Analytics JSON contains evidence IDs.

---

### NFR-006 — Extensibility

The architecture must support future analyzers.

**Acceptance Criteria:**

- Analyzers implement a common interface.
- New analyzers can be added without changing core orchestration logic.
- Output sections can be extended through templates.

---

## 9. System Architecture Specification

### 9.1 Logical Components

| Component | Responsibility |
|---|---|
| API Server | REST endpoints, request validation, artifact download |
| MCP Server | MCP tool exposure |
| Job Orchestrator | Async job lifecycle and stage execution |
| Repository Fetcher | Clone/fetch GitHub repo |
| Evidence Indexer | File metadata, evidence IDs, snippets |
| Technology Analyzer | Language/framework/tool detection |
| Intent Analyzer | Project purpose and business capability inference |
| Feature Analyzer | Feature grouping and capability extraction |
| Interface Analyzer | API, CLI, env, config, data contract discovery |
| Code Analyzer | Module, entrypoint, dependency, and code metrics |
| Commit Analyzer | Git history and change analytics |
| Test Analyzer | Test file and report discovery |
| Coverage Analyzer | Coverage file parsing |
| Spec Analyzer | HLD/LLD/SPEC/docs analysis |
| Diagram Generator | Mermaid/C4/deployment diagrams |
| Release Note Generator | Markdown/HTML/PDF generation |
| Storage Layer | Jobs, evidence, analytics, artifacts |
| Observability Layer | Logs, metrics, traces |

---

### 9.2 High-Level Flow

```mermaid
flowchart LR
    U[User or MCP Client] --> A[API / MCP Server]
    A --> J[Job Orchestrator]
    J --> G[GitHub Repository Fetcher]
    G --> E[Evidence Indexer]
    E --> T[Technology Analyzer]
    E --> I[Intent Analyzer]
    E --> F[Feature Analyzer]
    E --> C[Code Analyzer]
    E --> IF[Interface Analyzer]
    E --> CM[Commit Analyzer]
    E --> QA[Test and Coverage Analyzer]
    E --> S[Spec Analyzer]
    T --> AG[Analytics Aggregator]
    I --> AG
    F --> AG
    C --> AG
    IF --> AG
    CM --> AG
    QA --> AG
    S --> AG
    AG --> D[Diagram Generator]
    AG --> R[Release Note Generator]
    R --> O[Markdown / HTML / PDF Artifacts]
```

---

## 10. Data Model Specification

### 10.1 Job

```yaml
ScanJob:
  job_id: string
  repo_url: string
  branch: string | null
  tag: string | null
  commit_sha: string | null
  status: queued | running | completed | failed | cancelled
  stage: string
  created_at: datetime
  started_at: datetime | null
  completed_at: datetime | null
  error_message: string | null
```

### 10.2 Evidence

```yaml
EvidenceItem:
  evidence_id: string
  job_id: string
  source_type: file | commit | test_report | coverage_report | generated
  path: string | null
  commit_sha: string | null
  line_start: integer | null
  line_end: integer | null
  summary: string
  hash: string
```

### 10.3 Analytics Bundle

```yaml
AnalyticsBundle:
  job_id: string
  repository_metadata: object
  technology_inventory: list
  project_intent: object
  feature_inventory: list
  interface_inventory: list
  code_analytics: object
  commit_analytics: object
  test_analytics: object
  coverage_analytics: object
  spec_analytics: object
  diagram_inventory: list
  risk_notes: list
  known_gaps: list
```

### 10.4 Artifact

```yaml
GeneratedArtifact:
  artifact_id: string
  job_id: string
  artifact_type: markdown | html | pdf | json | diagram
  path: string
  created_at: datetime
  checksum: string
```

---

## 11. Job State Machine

```mermaid
stateDiagram-v2
    [*] --> QUEUED
    QUEUED --> FETCHING_REPOSITORY
    FETCHING_REPOSITORY --> INDEXING_EVIDENCE
    INDEXING_EVIDENCE --> ANALYZING_TECHNOLOGY
    ANALYZING_TECHNOLOGY --> ANALYZING_CODE
    ANALYZING_CODE --> ANALYZING_INTERFACES
    ANALYZING_INTERFACES --> ANALYZING_COMMITS
    ANALYZING_COMMITS --> ANALYZING_TESTS
    ANALYZING_TESTS --> ANALYZING_SPECS
    ANALYZING_SPECS --> GENERATING_DIAGRAMS
    GENERATING_DIAGRAMS --> GENERATING_RELEASE_NOTE
    GENERATING_RELEASE_NOTE --> RENDERING_ARTIFACTS
    RENDERING_ARTIFACTS --> COMPLETED

    FETCHING_REPOSITORY --> FAILED
    INDEXING_EVIDENCE --> FAILED
    ANALYZING_CODE --> FAILED
    RENDERING_ARTIFACTS --> FAILED
    QUEUED --> CANCELLED
    FETCHING_REPOSITORY --> CANCELLED
    ANALYZING_CODE --> CANCELLED
```

---

## 12. API Contract Specification

### 12.1 Create Scan Job

```http
POST /api/v1/scans
Content-Type: application/json
```

Request:

```json
{
  "repo_url": "https://github.com/example/project",
  "branch": "main",
  "release_name": "Release 1.0.0",
  "analysis_depth": "standard",
  "output_formats": ["markdown", "html", "pdf"]
}
```

Response:

```json
{
  "job_id": "scan_01HZABC123",
  "status": "queued",
  "status_url": "/api/v1/scans/scan_01HZABC123"
}
```

---

### 12.2 Get Scan Status

```http
GET /api/v1/scans/{job_id}
```

Response:

```json
{
  "job_id": "scan_01HZABC123",
  "status": "running",
  "stage": "analyzing_commits",
  "progress_percent": 62,
  "created_at": "2026-06-06T10:00:00Z",
  "started_at": "2026-06-06T10:00:03Z",
  "completed_at": null,
  "error_message": null
}
```

---

### 12.3 Get Analytics

```http
GET /api/v1/scans/{job_id}/analytics
```

Response:

```json
{
  "job_id": "scan_01HZABC123",
  "technology_inventory": [],
  "feature_inventory": [],
  "interface_inventory": [],
  "code_analytics": {},
  "commit_analytics": {},
  "test_analytics": {},
  "coverage_analytics": {},
  "spec_analytics": {}
}
```

---

## 13. MCP Tool Specification

### 13.1 Tool: `github_release_scan_start`

Purpose: Start a repository scan.

Input Schema:

```json
{
  "type": "object",
  "properties": {
    "repo_url": {"type": "string"},
    "branch": {"type": "string"},
    "tag": {"type": "string"},
    "commit_sha": {"type": "string"},
    "release_name": {"type": "string"},
    "analysis_depth": {"type": "string", "enum": ["fast", "standard", "deep"]},
    "output_formats": {
      "type": "array",
      "items": {"type": "string", "enum": ["markdown", "html", "pdf", "json"]}
    }
  },
  "required": ["repo_url"]
}
```

Output Schema:

```json
{
  "type": "object",
  "properties": {
    "job_id": {"type": "string"},
    "status": {"type": "string"},
    "message": {"type": "string"}
  }
}
```

---

### 13.2 Tool: `github_release_scan_status`

Purpose: Retrieve scan status.

Input:

```json
{
  "job_id": "scan_01HZABC123"
}
```

Output:

```json
{
  "job_id": "scan_01HZABC123",
  "status": "running",
  "stage": "analyzing_code",
  "progress_percent": 45
}
```

---

### 13.3 Tool: `github_release_get_artifact`

Purpose: Retrieve generated artifact metadata.

Input:

```json
{
  "job_id": "scan_01HZABC123",
  "artifact_type": "pdf"
}
```

Output:

```json
{
  "artifact_type": "pdf",
  "path": "/data/artifacts/scan_01HZABC123/release-note.pdf",
  "available": true
}
```

---

## 14. Release Note Content Specification

### 14.1 Required Release Note Layout

```text
Cover Page
Document Control
Executive Summary
Release Overview
Repository Overview
Project Intent
Technology Inventory
Architecture Overview
C4 Context Diagram
C4 Container Diagram
C4 Component Diagram
Deployment Topology
Feature Inventory
Interface Inventory
Code Analytics
Test Analytics
Coverage Analytics
Commit Analytics
Quality and Risk Assessment
Known Gaps
Evidence Traceability
Appendix
```

### 14.2 Tone and Style

The release note must be:

- Professional
- Commercial-grade
- Evidence-backed
- Concise but informative
- Suitable for architecture review
- Suitable for release governance
- Suitable for executive summary review

The release note must not be:

- A raw Git log dump
- A plain README rewrite
- A generic AI-generated essay
- Unsupported by repository evidence

---

## 15. Diagram Specification

### 15.1 Mermaid Flow Diagram

Must show the runtime flow of the project when inferable.

### 15.2 C4 Context Diagram

Must show:

- User or external actor
- Target system
- External systems or repositories
- External APIs or data stores when inferable

### 15.3 C4 Container Diagram

Must show:

- API container
- Worker container
- Database
- Object/artifact storage
- MCP server surface
- GitHub source

### 15.4 C4 Component Diagram

Must show internal components such as:

- Repo fetcher
- Evidence indexer
- Analyzers
- Diagram generator
- Release note generator
- PDF renderer

### 15.5 Deployment Diagram

Must show deployment topology for the scanned project when Kubernetes, Docker, Helm, or cloud deployment evidence exists.

---

## 16. Quality Gates

### 16.1 Scan Quality Gates

| Gate | Pass Condition |
|---|---|
| Repository fetched | Git metadata and file tree available |
| Evidence indexed | Files and commits indexed |
| Technology detection | At least primary language detected or unknown stated |
| Code analytics | Source files counted and grouped |
| Commit analytics | Commit range analyzed |
| Release note generated | Markdown artifact exists |
| PDF generated | PDF artifact exists when requested |

### 16.2 Release Note Quality Gates

| Gate | Pass Condition |
|---|---|
| Professional structure | Required sections present |
| Evidence-backed | Key claims include evidence IDs |
| Missing-data transparency | Missing coverage/test/spec data explicitly reported |
| Diagram validity | Mermaid syntax validated where possible |
| Artifact integrity | Output files have checksum |

---

## 17. Test Strategy

### 17.1 Unit Tests

Required test coverage for:

- URL validation
- Git fetcher
- Evidence indexer
- Technology analyzer
- Commit analyzer
- Coverage parser
- Test report parser
- Diagram generator
- Release note generator
- MCP tool schema validation
- API request/response validation

### 17.2 Integration Tests

Required integration tests:

- Scan a small public Python repository
- Scan a repository with no coverage data
- Scan a repository with coverage data
- Scan a repository with multiple specs
- Generate Markdown artifact
- Generate PDF artifact
- Invoke scan through REST
- Invoke scan through MCP

### 17.3 Contract Tests

Required contract tests:

- REST API schemas
- MCP tool input/output schemas
- Analytics JSON schema
- Artifact metadata schema

### 17.4 Negative Tests

Required negative tests:

- Invalid GitHub URL
- Non-existent repository
- Oversized repository
- Unsupported file encodings
- Broken coverage XML
- Missing README
- Missing tests
- PDF render failure

---

## 18. Security Specification

### 18.1 Repository Safety

The system must treat every scanned repository as untrusted input.

Rules:

- Do not execute code by default.
- Do not run package install commands by default.
- Do not run tests by default.
- Do not source environment files.
- Do not expose secrets found in files.
- Redact credentials from generated artifacts.

### 18.2 Secret Redaction

The system must redact values matching common secret patterns:

- API keys
- Bearer tokens
- Passwords
- Private keys
- Cloud credentials
- Database credentials
- Kubernetes secrets
- `.env` values

### 18.3 Output Safety

Generated reports must not include raw secrets or sensitive credentials.

---

## 19. Configuration Specification

Environment variables:

```env
APP_NAME=github-release-note-agent
APP_MODE=api_mcp
DATABASE_URL=postgresql://user:password@postgres:5432/release_agent
REDIS_URL=redis://redis:6379/0
ARTIFACT_ROOT=/data/artifacts
WORKSPACE_ROOT=/data/workspaces
MAX_REPO_SIZE_MB=500
MAX_FILE_SIZE_MB=10
ENABLE_LLM_SUMMARY=true
ENABLE_PDF_RENDERING=true
ENABLE_MCP_SERVER=true
ENABLE_REST_API=true
OTEL_ENABLED=false
LANGFUSE_ENABLED=false
```

---

## 20. Storage Specification

### 20.1 PostgreSQL Tables

Required logical tables:

- `scan_jobs`
- `scan_stages`
- `evidence_items`
- `technology_inventory`
- `feature_inventory`
- `interface_inventory`
- `code_analytics`
- `commit_analytics`
- `test_analytics`
- `coverage_analytics`
- `spec_analytics`
- `generated_artifacts`

### 20.2 File Storage

Required directory layout:

```text
/data
  /workspaces
    /{job_id}
      /repo
  /artifacts
    /{job_id}
      analytics.json
      release-note.md
      release-note.html
      release-note.pdf
      diagrams/
  /logs
```

---

## 21. Observability Specification

The system must produce structured logs for each stage.

Example:

```json
{
  "event": "stage_completed",
  "job_id": "scan_01HZABC123",
  "stage": "analyzing_commits",
  "duration_ms": 1420,
  "status": "success"
}
```

Metrics:

- `scan_job_total`
- `scan_job_failed_total`
- `scan_duration_seconds`
- `analyzer_duration_seconds`
- `artifact_generation_duration_seconds`
- `repo_size_bytes`
- `evidence_items_total`

---

## 22. Error Handling Specification

Errors must be structured.

```json
{
  "error_code": "REPO_FETCH_FAILED",
  "message": "Repository could not be cloned",
  "details": {
    "repo_url": "https://github.com/example/missing"
  },
  "retryable": false
}
```

Required error codes:

| Error Code | Meaning |
|---|---|
| `INVALID_REPO_URL` | Repo URL is malformed or unsupported |
| `REPO_FETCH_FAILED` | Repo could not be fetched |
| `REPO_TOO_LARGE` | Repo exceeds configured size limit |
| `ANALYZER_FAILED` | Analyzer failed unexpectedly |
| `COVERAGE_PARSE_FAILED` | Coverage file could not be parsed |
| `DIAGRAM_GENERATION_FAILED` | Diagram generation failed |
| `PDF_RENDER_FAILED` | PDF rendering failed |
| `ARTIFACT_NOT_FOUND` | Requested artifact does not exist |

---

## 23. Implementation Phases

### Phase 1 — Foundation

Deliver:

- FastAPI app
- MCP server skeleton
- Job model
- Repository fetcher
- Workspace manager
- Basic status API

### Phase 2 — Evidence and Core Analysis

Deliver:

- Evidence indexer
- Technology analyzer
- Code analyzer
- Commit analyzer
- Spec document scanner

### Phase 3 — Quality and Interface Analysis

Deliver:

- Test analyzer
- Coverage analyzer
- Interface analyzer
- Feature analyzer
- Intent analyzer

### Phase 4 — Release Note Generation

Deliver:

- Markdown generator
- Mermaid diagrams
- C4 diagrams
- HTML renderer
- PDF renderer

### Phase 5 — Production Hardening

Deliver:

- PostgreSQL persistence
- Redis queue
- OpenTelemetry support
- Error handling hardening
- Dockerfile
- Helm chart
- Acceptance test suite

---

## 24. Definition of Done

The agent is considered complete for MVP when:

1. A public GitHub repository can be scanned asynchronously.
2. REST APIs expose scan creation, status, analytics, and artifacts.
3. MCP tools expose scan creation, status, analytics, and artifact retrieval.
4. The agent detects technologies and tools with evidence references.
5. The agent identifies project intent and features.
6. The agent analyzes commit history.
7. The agent detects test and coverage evidence when available.
8. The agent reads HLD, LLD, SPEC.md, and nested specs when available.
9. The agent generates Mermaid and C4 diagrams.
10. The agent generates Markdown, HTML, and PDF release notes.
11. Missing evidence is clearly reported.
12. Generated release note passes quality gates.
13. Basic unit and integration tests pass.
14. Logs and job-stage status are available.

---

## 25. Acceptance Test Scenarios

### ATS-001 — Scan Valid Public Repo

Given a valid public GitHub repository URL, when the user starts a scan, then the system creates a job and eventually generates analytics and release artifacts.

### ATS-002 — Missing Coverage Data

Given a repository without coverage data, when the release note is generated, then the coverage section states that coverage evidence was not found.

### ATS-003 — Repository With Specs

Given a repository with HLD, LLD, and SPEC.md files, when the scan completes, then the spec analytics section lists those files and summarizes their role.

### ATS-004 — MCP Scan Invocation

Given an MCP client, when it calls `github_release_scan_start`, then the system starts a scan and returns a job ID.

### ATS-005 — Professional PDF Generation

Given completed analytics, when the user requests PDF output, then the system generates a professional PDF release note with diagrams and analytics sections.

---

## 26. Traceability Matrix

| Requirement | Design Component | Test Type |
|---|---|---|
| FR-001 | API Server, Job Orchestrator | API integration test |
| FR-002 | Repository Fetcher | Unit + integration test |
| FR-003 | Technology Analyzer | Unit test |
| FR-004 | Intent Analyzer | Unit + golden-output test |
| FR-005 | Feature Analyzer | Unit + golden-output test |
| FR-006 | Interface Analyzer | Unit test |
| FR-007 | Code Analyzer | Unit test |
| FR-008 | Commit Analyzer | Unit + integration test |
| FR-009 | Coverage Analyzer | Unit test |
| FR-010 | Test Analyzer | Unit test |
| FR-011 | Spec Analyzer | Unit test |
| FR-012 | Diagram Generator | Snapshot test |
| FR-013 | Release Note Generator | Golden-file test |
| FR-014 | REST API | Contract test |
| FR-015 | MCP Server | Contract test |

---

## 27. Open Questions

1. Should private GitHub repositories be supported in Phase 2?
2. Should the agent run tests optionally in a sandboxed container?
3. Should the agent create GitHub releases automatically?
4. Should generated release notes be pushed back to the repository?
5. Should SBOM and vulnerability scanning be added?
6. Should multiple repositories be analyzed together for monorepo or platform release notes?
7. Should BOS Genesis memory and observability components be optional runtime plugins?

---

## 28. Future Enhancements

- Private repository support
- GitHub App authentication
- GitHub Actions artifact retrieval
- SBOM generation
- Vulnerability summary
- License inventory
- ADR extraction
- LLM-based architecture critique
- Cross-release comparison
- Pull request impact summary
- Automated release draft creation
- Integration with BOS Genesis observability stack
- Integration with Langfuse, SigNoz, PostgreSQL, ClickHouse, MongoDB, Qdrant, and n8n

---

## 29. Summary

This specification defines a Python-based GitHub Release Note Intelligence Agent that operates both as a REST API service and MCP server. It scans public GitHub repositories, builds an evidence-backed understanding of the project, analyzes code, commits, tests, coverage, specs, interfaces, and architecture, and generates a professional release note package with diagrams and analytics.

This `SPEC.md` should be treated as the working contract for spec-driven development. Implementation should proceed only against requirements, acceptance criteria, and quality gates defined here.
