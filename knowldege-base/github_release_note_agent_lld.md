# Low-Level Design (LLD): GitHub Release Note Intelligence Agent

**Document Version:** 1.0  
**Target Implementation:** Python 3.12+  
**Runtime Modes:** REST API server, MCP server, CLI worker  
**Primary Goal:** Scan a public GitHub repository, understand the project, analyze code/test/coverage/spec/history/interfaces, and generate professional release notes with architecture and analytics diagrams.

---

## 1. Purpose

This LLD defines the implementation design for a Python-based intelligent release-note generation agent. The agent can run as:

1. A REST API service for web/UI or automation clients.
2. An MCP server so Codex, Kiro, Claude Code, or other agentic clients can call it as a governed tool.
3. An async worker service for long-running GitHub scan and report-generation jobs.
4. A CLI utility for local development and debugging.

The agent will inspect a GitHub public repository, build a structured understanding of the project, extract technical and release evidence, generate diagrams, run analytics, and produce industry-standard release notes in Markdown, HTML, and PDF formats.

---

## 2. Scope

### 2.1 In Scope

- Clone or fetch a public GitHub repository.
- Read repository metadata, file tree, README files, specs, HLD, LLD, and module-level `specs.md` files.
- Detect technology stack, frameworks, package managers, build tools, CI tools, test tools, coverage reports, and deployment artifacts.
- Analyze source code structure, modules, public interfaces, API routes, classes, functions, dependencies, and configuration.
- Read Git commit history, tags, branches, releases, and pull-request metadata when available.
- Read unit test data and code coverage data when available.
- Generate evidence-backed release-note sections.
- Generate Mermaid flow diagrams, C4-style diagrams, deployment diagrams, module diagrams, and interface diagrams.
- Generate code analytics, interface analytics, commit analytics, test analytics, and coverage analytics.
- Expose all major capabilities through REST API and MCP tools.
- Support async job execution with resumable job states.
- Produce professional Markdown, HTML, and PDF outputs.

### 2.2 Out of Scope for Version 1

- Private GitHub repositories requiring enterprise SSO.
- Direct code modification or pull-request creation.
- Full static security scanning equivalent to SAST products.
- Runtime tracing from deployed applications.
- Legal/compliance certification of generated release notes.
- Guaranteed 100% semantic correctness for all languages.

---

## 3. Key Design Principles

1. **Evidence first:** Every generated claim should be traceable to repository files, commits, tests, or tool outputs.
2. **Async by default:** Repository scans and release-note generation may be long-running.
3. **Modular analyzers:** Each analyzer is independently testable and replaceable.
4. **MCP compatible:** The same backend capabilities should be callable through MCP tools.
5. **Human-reviewable output:** The final release note should be professional but clearly mark unknowns, assumptions, and missing evidence.
6. **Safe repository execution:** By default, the agent reads and analyzes. It should not execute arbitrary repo scripts unless explicitly enabled in sandbox mode.
7. **Diagram as code:** Mermaid/C4 diagrams should be generated as text artifacts and rendered into the final PDF.
8. **Template driven:** Release-note layout should be controlled through configurable templates.

---

## 4. Runtime Architecture

```mermaid
flowchart LR
    U[User / UI / Codex / Kiro] --> API[FastAPI REST API]
    U --> MCP[MCP Server]
    CLI[CLI Client] --> API

    API --> JOB[Job Orchestrator]
    MCP --> JOB

    JOB --> Q[(Redis / Valkey Queue)]
    Q --> W1[Repository Scan Worker]
    Q --> W2[Analyzer Worker]
    Q --> W3[Report Generation Worker]

    W1 --> GH[GitHub Public Repo]
    W1 --> FS[(Workspace Storage)]
    W2 --> FS
    W2 --> DB[(PostgreSQL)]
    W2 --> OBJ[(Artifact Storage)]
    W3 --> DB
    W3 --> OBJ

    W3 --> OUT[Markdown / HTML / PDF / Diagrams]
```

---

## 5. Component Responsibilities

| Component | Responsibility | Implementation |
|---|---|---|
| REST API | Submit jobs, check status, download artifacts | FastAPI |
| MCP Server | Expose scan/analyze/generate tools to agentic clients | FastMCP or official MCP Python SDK |
| Job Orchestrator | Create job plan, manage state transitions, enqueue tasks | Python service layer |
| Repository Fetcher | Clone repo, checkout tag/branch/commit, collect metadata | GitPython / pygit2 / subprocess git |
| File Inventory Analyzer | Build file tree, classify files, detect important documents | pathlib + heuristics |
| Technology Detector | Detect languages, frameworks, tools, package managers | custom detectors + package files |
| Intent Analyzer | Infer project purpose from README/specs/code/package metadata | rules + optional LLM summarization |
| Feature Analyzer | Extract project features from docs, APIs, modules, tests | rules + optional LLM |
| Interface Analyzer | Identify REST APIs, CLIs, MCP endpoints, configs, inputs/outputs | AST + framework detectors |
| Code Analyzer | Extract modules, classes, functions, complexity, dependency graph | AST/parsers/radon/networkx |
| Test Analyzer | Parse unit test files and test reports | pytest/junit XML/cobertura |
| Coverage Analyzer | Parse coverage outputs and summarize coverage quality | coverage.xml, lcov.info, JaCoCo XML |
| Commit Analyzer | Analyze commits, tags, release ranges, authors, churn | Git history parser |
| Spec Analyzer | Read HLD, LLD, specs.md, module specs | Markdown parser |
| Diagram Generator | Generate Mermaid/C4/deployment diagrams | Mermaid text + optional renderer |
| Release Note Generator | Compose professional release note from evidence model | Jinja2 templates + optional LLM |
| PDF Renderer | Convert Markdown/HTML to PDF | WeasyPrint / Playwright / wkhtmltopdf |
| Evidence Store | Persist analysis outputs and traceability records | PostgreSQL + JSONB |
| Artifact Store | Store generated reports, diagrams, raw evidence | local FS / S3-compatible storage |

---

## 6. Suggested Repository Structure

```text
github-release-note-agent/
├── README.md
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── helm/
│   └── github-release-note-agent/
├── src/
│   └── grna/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── logging_config.py
│       ├── api/
│       │   ├── app.py
│       │   ├── routes_jobs.py
│       │   ├── routes_artifacts.py
│       │   └── schemas.py
│       ├── mcp/
│       │   ├── server.py
│       │   ├── tools.py
│       │   └── schemas.py
│       ├── cli/
│       │   └── main.py
│       ├── jobs/
│       │   ├── orchestrator.py
│       │   ├── states.py
│       │   ├── queue.py
│       │   └── worker.py
│       ├── github/
│       │   ├── client.py
│       │   ├── clone.py
│       │   ├── commits.py
│       │   └── releases.py
│       ├── analyzers/
│       │   ├── base.py
│       │   ├── inventory.py
│       │   ├── technology.py
│       │   ├── intent.py
│       │   ├── features.py
│       │   ├── interfaces.py
│       │   ├── code.py
│       │   ├── tests.py
│       │   ├── coverage.py
│       │   ├── commits.py
│       │   ├── specs.py
│       │   └── dependencies.py
│       ├── diagrams/
│       │   ├── mermaid.py
│       │   ├── c4.py
│       │   ├── deployment.py
│       │   └── topology.py
│       ├── reports/
│       │   ├── generator.py
│       │   ├── templates/
│       │   │   ├── release_note.md.j2
│       │   │   ├── release_note.html.j2
│       │   │   └── executive_summary.md.j2
│       │   ├── renderer_pdf.py
│       │   └── renderer_html.py
│       ├── llm/
│       │   ├── provider.py
│       │   ├── prompts.py
│       │   └── guardrails.py
│       ├── storage/
│       │   ├── db.py
│       │   ├── models.py
│       │   ├── repositories.py
│       │   └── artifacts.py
│       ├── observability/
│       │   ├── tracing.py
│       │   ├── metrics.py
│       │   └── audit.py
│       └── utils/
│           ├── hashing.py
│           ├── markdown.py
│           ├── shell.py
│           └── paths.py
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## 7. Main Execution Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as REST API / MCP Tool
    participant Orch as Job Orchestrator
    participant Queue
    participant Worker
    participant Repo as GitHub Repo
    participant DB as Evidence DB
    participant Artifact as Artifact Store

    Client->>API: submit_release_note_job(repo_url, ref, options)
    API->>Orch: create job
    Orch->>DB: persist job=PENDING
    Orch->>Queue: enqueue repository_scan
    API-->>Client: job_id

    Worker->>Queue: consume repository_scan
    Worker->>Repo: clone/fetch repository
    Worker->>DB: persist repository metadata
    Worker->>Queue: enqueue analyzers

    Worker->>Queue: consume analyzers
    Worker->>DB: persist technology/code/test/coverage/commit/spec evidence
    Worker->>Artifact: store raw analyzer outputs
    Worker->>Queue: enqueue generate_report

    Worker->>Queue: consume generate_report
    Worker->>DB: load evidence model
    Worker->>Artifact: write markdown/html/pdf/diagrams
    Worker->>DB: job=COMPLETED

    Client->>API: get job status / download report
```

---

## 8. Job State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> CLONING
    CLONING --> INVENTORY_ANALYSIS
    INVENTORY_ANALYSIS --> TECHNOLOGY_ANALYSIS
    TECHNOLOGY_ANALYSIS --> CODE_ANALYSIS
    CODE_ANALYSIS --> TEST_ANALYSIS
    TEST_ANALYSIS --> COVERAGE_ANALYSIS
    COVERAGE_ANALYSIS --> COMMIT_ANALYSIS
    COMMIT_ANALYSIS --> SPEC_ANALYSIS
    SPEC_ANALYSIS --> DIAGRAM_GENERATION
    DIAGRAM_GENERATION --> REPORT_GENERATION
    REPORT_GENERATION --> PDF_RENDERING
    PDF_RENDERING --> COMPLETED

    CLONING --> FAILED
    INVENTORY_ANALYSIS --> FAILED
    TECHNOLOGY_ANALYSIS --> FAILED
    CODE_ANALYSIS --> FAILED
    TEST_ANALYSIS --> PARTIAL_SUCCESS
    COVERAGE_ANALYSIS --> PARTIAL_SUCCESS
    COMMIT_ANALYSIS --> FAILED
    SPEC_ANALYSIS --> PARTIAL_SUCCESS
    DIAGRAM_GENERATION --> PARTIAL_SUCCESS
    REPORT_GENERATION --> FAILED
    PDF_RENDERING --> PARTIAL_SUCCESS

    PARTIAL_SUCCESS --> COMPLETED
    FAILED --> [*]
    COMPLETED --> [*]
```

### 8.1 Job State Definitions

| State | Meaning |
|---|---|
| PENDING | Job created but no worker picked it up |
| CLONING | Repository is being cloned/fetched |
| INVENTORY_ANALYSIS | File tree and document inventory are being built |
| TECHNOLOGY_ANALYSIS | Languages/frameworks/tools are being detected |
| CODE_ANALYSIS | Source modules, functions, dependencies, and interfaces are being analyzed |
| TEST_ANALYSIS | Unit/integration tests and reports are being parsed |
| COVERAGE_ANALYSIS | Coverage artifacts are being parsed |
| COMMIT_ANALYSIS | Git history and release range are being analyzed |
| SPEC_ANALYSIS | HLD/LLD/specs.md files are being analyzed |
| DIAGRAM_GENERATION | Mermaid/C4/deployment diagrams are being generated |
| REPORT_GENERATION | Release note Markdown/HTML is being generated |
| PDF_RENDERING | PDF report is being rendered |
| COMPLETED | Final artifacts are available |
| PARTIAL_SUCCESS | Non-critical analyzer failed but report can continue |
| FAILED | Critical failure prevents report generation |

---

## 9. Data Model

### 9.1 Logical Entity Model

```mermaid
erDiagram
    REPOSITORY ||--o{ RELEASE_JOB : has
    RELEASE_JOB ||--o{ JOB_EVENT : records
    RELEASE_JOB ||--o{ ANALYSIS_RESULT : produces
    RELEASE_JOB ||--o{ ARTIFACT : creates
    ANALYSIS_RESULT ||--o{ EVIDENCE_ITEM : contains
    REPOSITORY ||--o{ COMMIT_RECORD : has
    REPOSITORY ||--o{ FILE_RECORD : has
```

### 9.2 PostgreSQL Tables

#### `repositories`

```sql
CREATE TABLE repositories (
    id UUID PRIMARY KEY,
    repo_url TEXT NOT NULL,
    owner TEXT,
    name TEXT,
    default_branch TEXT,
    visibility TEXT DEFAULT 'public',
    provider TEXT DEFAULT 'github',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(repo_url)
);
```

#### `release_jobs`

```sql
CREATE TABLE release_jobs (
    id UUID PRIMARY KEY,
    repository_id UUID REFERENCES repositories(id),
    requested_ref TEXT,
    from_ref TEXT,
    to_ref TEXT,
    status TEXT NOT NULL,
    options JSONB NOT NULL DEFAULT '{}'::jsonb,
    progress_percent INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

#### `job_events`

```sql
CREATE TABLE job_events (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES release_jobs(id),
    event_type TEXT NOT NULL,
    state TEXT,
    message TEXT,
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### `file_records`

```sql
CREATE TABLE file_records (
    id UUID PRIMARY KEY,
    repository_id UUID REFERENCES repositories(id),
    job_id UUID REFERENCES release_jobs(id),
    path TEXT NOT NULL,
    file_type TEXT,
    language TEXT,
    size_bytes BIGINT,
    sha256 TEXT,
    is_test BOOLEAN DEFAULT false,
    is_spec BOOLEAN DEFAULT false,
    is_config BOOLEAN DEFAULT false,
    classification JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### `commit_records`

```sql
CREATE TABLE commit_records (
    id UUID PRIMARY KEY,
    repository_id UUID REFERENCES repositories(id),
    job_id UUID REFERENCES release_jobs(id),
    sha TEXT NOT NULL,
    author_name TEXT,
    author_email TEXT,
    committed_at TIMESTAMPTZ,
    message TEXT,
    files_changed INT,
    insertions INT,
    deletions INT,
    tags JSONB DEFAULT '[]'::jsonb,
    classification JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### `analysis_results`

```sql
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES release_jobs(id),
    analyzer_name TEXT NOT NULL,
    analyzer_version TEXT,
    status TEXT NOT NULL,
    summary JSONB DEFAULT '{}'::jsonb,
    metrics JSONB DEFAULT '{}'::jsonb,
    warnings JSONB DEFAULT '[]'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### `evidence_items`

```sql
CREATE TABLE evidence_items (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES release_jobs(id),
    analysis_result_id UUID REFERENCES analysis_results(id),
    evidence_type TEXT NOT NULL,
    title TEXT,
    source_path TEXT,
    source_ref TEXT,
    line_start INT,
    line_end INT,
    commit_sha TEXT,
    confidence NUMERIC(4,3),
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### `artifacts`

```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES release_jobs(id),
    artifact_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT,
    storage_uri TEXT NOT NULL,
    size_bytes BIGINT,
    sha256 TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 10. Core Pydantic Models

```python
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from typing import Any, Optional
from uuid import UUID

class JobStatus(str, Enum):
    PENDING = "PENDING"
    CLONING = "CLONING"
    INVENTORY_ANALYSIS = "INVENTORY_ANALYSIS"
    TECHNOLOGY_ANALYSIS = "TECHNOLOGY_ANALYSIS"
    CODE_ANALYSIS = "CODE_ANALYSIS"
    TEST_ANALYSIS = "TEST_ANALYSIS"
    COVERAGE_ANALYSIS = "COVERAGE_ANALYSIS"
    COMMIT_ANALYSIS = "COMMIT_ANALYSIS"
    SPEC_ANALYSIS = "SPEC_ANALYSIS"
    DIAGRAM_GENERATION = "DIAGRAM_GENERATION"
    REPORT_GENERATION = "REPORT_GENERATION"
    PDF_RENDERING = "PDF_RENDERING"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"

class ReleaseNoteJobRequest(BaseModel):
    repo_url: HttpUrl
    ref: Optional[str] = None
    from_ref: Optional[str] = None
    to_ref: Optional[str] = None
    include_pdf: bool = True
    include_html: bool = True
    include_mermaid: bool = True
    include_c4: bool = True
    include_commit_analytics: bool = True
    include_code_analytics: bool = True
    include_test_analytics: bool = True
    execute_tests: bool = False
    max_repo_size_mb: int = 500
    llm_enabled: bool = True
    output_profile: str = "enterprise"

class ReleaseNoteJobResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    status_url: str

class JobStatusResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    progress_percent: int
    current_step: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)

class EvidenceItem(BaseModel):
    evidence_type: str
    title: str
    source_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    commit_sha: Optional[str] = None
    confidence: float = 0.0
    content: dict[str, Any] = Field(default_factory=dict)
```

---

## 11. REST API Design

### 11.1 Submit Release Note Job

```http
POST /api/v1/release-notes/jobs
Content-Type: application/json
```

Request:

```json
{
  "repo_url": "https://github.com/example/payments-api",
  "ref": "main",
  "from_ref": "v2.3.9",
  "to_ref": "v2.4.1",
  "include_pdf": true,
  "include_html": true,
  "include_mermaid": true,
  "include_c4": true,
  "include_commit_analytics": true,
  "include_code_analytics": true,
  "include_test_analytics": true,
  "execute_tests": false,
  "output_profile": "enterprise"
}
```

Response:

```json
{
  "job_id": "7f10fb4a-0b6e-4e65-8af4-7d3e8451fb2f",
  "status": "PENDING",
  "status_url": "/api/v1/release-notes/jobs/7f10fb4a-0b6e-4e65-8af4-7d3e8451fb2f"
}
```

### 11.2 Get Job Status

```http
GET /api/v1/release-notes/jobs/{job_id}
```

### 11.3 List Job Artifacts

```http
GET /api/v1/release-notes/jobs/{job_id}/artifacts
```

### 11.4 Download Artifact

```http
GET /api/v1/release-notes/jobs/{job_id}/artifacts/{artifact_id}/download
```

### 11.5 Get Evidence Model

```http
GET /api/v1/release-notes/jobs/{job_id}/evidence
```

### 11.6 Cancel Job

```http
POST /api/v1/release-notes/jobs/{job_id}/cancel
```

---

## 12. MCP Server Design

The MCP server exposes the same capability surface for agentic clients. The MCP server should not directly perform heavy work inline. It should create jobs, return job IDs, and allow polling/downloading artifacts.

### 12.1 MCP Tools

| Tool Name | Purpose |
|---|---|
| `github_release_note_submit_job` | Submit a repo scan and release-note generation job |
| `github_release_note_get_job_status` | Poll current job status |
| `github_release_note_list_artifacts` | List generated artifacts |
| `github_release_note_get_artifact` | Retrieve artifact content or download path |
| `github_release_note_get_evidence` | Retrieve structured evidence model |
| `github_release_note_cancel_job` | Cancel a running job |
| `github_repo_scan_only` | Run only repository understanding scan |
| `github_commit_analytics_only` | Run only commit analytics |
| `github_code_analytics_only` | Run only code analytics |

### 12.2 MCP Tool Contract Example

```json
{
  "name": "github_release_note_submit_job",
  "description": "Analyze a public GitHub repository and generate professional release notes with diagrams and analytics.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "repo_url": {"type": "string"},
      "ref": {"type": "string"},
      "from_ref": {"type": "string"},
      "to_ref": {"type": "string"},
      "include_pdf": {"type": "boolean", "default": true},
      "output_profile": {"type": "string", "default": "enterprise"}
    },
    "required": ["repo_url"]
  }
}
```

### 12.3 MCP Server Internal Flow

```mermaid
flowchart TD
    A[MCP Client] --> B[MCP Tool: submit job]
    B --> C[Validate input]
    C --> D[Call Job Orchestrator]
    D --> E[Persist job]
    E --> F[Enqueue async work]
    F --> G[Return job_id]

    A --> H[MCP Tool: get status]
    H --> I[Read job state]
    I --> J[Return progress and artifacts]
```

---

## 13. Analyzer Framework

### 13.1 Base Analyzer Interface

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

class AnalyzerContext:
    def __init__(
        self,
        job_id: str,
        repo_path: Path,
        workspace_path: Path,
        options: dict[str, Any],
    ):
        self.job_id = job_id
        self.repo_path = repo_path
        self.workspace_path = workspace_path
        self.options = options

class AnalyzerResult:
    def __init__(
        self,
        analyzer_name: str,
        status: str,
        summary: dict[str, Any],
        metrics: dict[str, Any],
        evidence: list[dict[str, Any]],
        warnings: list[str] | None = None,
    ):
        self.analyzer_name = analyzer_name
        self.status = status
        self.summary = summary
        self.metrics = metrics
        self.evidence = evidence
        self.warnings = warnings or []

class BaseAnalyzer(ABC):
    name: str
    version: str = "1.0"

    @abstractmethod
    async def run(self, context: AnalyzerContext) -> AnalyzerResult:
        raise NotImplementedError
```

### 13.2 Analyzer Execution Order

```mermaid
flowchart LR
    INV[Inventory Analyzer] --> TECH[Technology Analyzer]
    INV --> SPEC[Spec Analyzer]
    TECH --> CODE[Code Analyzer]
    CODE --> IFACE[Interface Analyzer]
    INV --> TEST[Test Analyzer]
    TEST --> COV[Coverage Analyzer]
    INV --> DEP[Dependency Analyzer]
    INV --> COMMIT[Commit Analyzer]
    TECH --> DIAG[Diagram Generator]
    CODE --> DIAG
    IFACE --> DIAG
    COMMIT --> REPORT[Release Note Generator]
    DIAG --> REPORT
    SPEC --> REPORT
    TEST --> REPORT
    COV --> REPORT
```

---

## 14. Analyzer Details

## 14.1 Repository Inventory Analyzer

### Responsibility

- Traverse full repository tree.
- Classify source, test, config, documentation, CI/CD, deployment, and report files.
- Identify high-value documents: `README.md`, `CHANGELOG.md`, `HLD.md`, `LLD.md`, `specs.md`, `docs/**/*.md`, `openapi.yaml`, `package.json`, `pyproject.toml`, etc.

### Inputs

- Local cloned repository path.

### Outputs

```json
{
  "total_files": 247,
  "source_files": 83,
  "test_files": 41,
  "documentation_files": 18,
  "deployment_files": 12,
  "coverage_files": 2,
  "important_documents": [
    "README.md",
    "docs/HLD.md",
    "src/payments/specs.md"
  ]
}
```

### Detection Rules

| Category | Patterns |
|---|---|
| Python source | `*.py`, excluding tests |
| JavaScript/TypeScript | `*.js`, `*.jsx`, `*.ts`, `*.tsx` |
| Java | `*.java` |
| Tests | `test_*.py`, `*_test.py`, `tests/**`, `*.spec.ts`, `*.test.ts` |
| Coverage | `coverage.xml`, `lcov.info`, `jacoco.xml`, `.coverage` |
| Deployment | `Dockerfile`, `docker-compose.yml`, `helm/**`, `k8s/**`, `*.yaml` with Kubernetes kind |
| Specs | `specs.md`, `HLD.md`, `LLD.md`, `.kiro/specs/**` |
| CI/CD | `.github/workflows/**`, `.gitlab-ci.yml`, `Jenkinsfile` |

---

## 14.2 Technology Detector

### Responsibility

Detect project technology stack and tools.

### Detection Inputs

| File | Detection |
|---|---|
| `pyproject.toml` | Python project, dependencies, build backend |
| `requirements.txt` | Python dependencies |
| `package.json` | Node/React/Angular/Vue/Nest/Express tools |
| `pom.xml` | Java Maven |
| `build.gradle` | Java/Kotlin Gradle |
| `go.mod` | Go project |
| `Cargo.toml` | Rust project |
| `Dockerfile` | Container runtime |
| `helm/Chart.yaml` | Helm chart |
| `.github/workflows/*.yml` | CI/CD tooling |

### Output Model

```json
{
  "primary_language": "Python",
  "languages": ["Python", "Markdown", "YAML", "Shell"],
  "frameworks": ["FastAPI", "Pydantic", "SQLAlchemy"],
  "test_tools": ["pytest", "coverage.py"],
  "build_tools": ["uv", "setuptools"],
  "deployment_tools": ["Docker", "Helm", "Kubernetes"],
  "ci_tools": ["GitHub Actions"],
  "observability_tools": ["OpenTelemetry", "Langfuse"]
}
```

---

## 14.3 Intent Analyzer

### Responsibility

Infer project purpose and business/technical intent from:

- README title and description.
- Repository name.
- Package metadata.
- Specs/HLD/LLD.
- Main API routes or CLI commands.
- Domain-specific terms.

### Algorithm

1. Read primary documentation files.
2. Extract title, overview, feature sections, architecture sections.
3. Cross-check package names and executable entry points.
4. Cross-check source modules and API routes.
5. Produce intent summary with confidence score.

### Output

```json
{
  "intent_summary": "The project provides a Kubernetes-aware release automation agent that analyzes repository evidence and generates professional release notes.",
  "domain": "DevOps / Release Engineering / Agentic AI",
  "confidence": 0.86,
  "supporting_evidence": [
    {"path": "README.md", "lines": [1, 20]},
    {"path": "src/grna/api/routes_jobs.py", "lines": [10, 72]}
  ]
}
```

---

## 14.4 Feature Analyzer

### Responsibility

Extract project features from documentation, APIs, CLI commands, test names, and modules.

### Feature Sources

- Markdown headings under `Features`, `Capabilities`, `Use Cases`.
- FastAPI route names and tags.
- CLI command definitions.
- Test class/function names.
- Public service classes.

### Output

```json
{
  "features": [
    {
      "name": "Repository Scan",
      "description": "Clones and inventories a GitHub repository.",
      "source": "src/grna/github/clone.py",
      "confidence": 0.91
    },
    {
      "name": "Release Note PDF Generation",
      "description": "Generates enterprise release-note PDF artifacts.",
      "source": "src/grna/reports/renderer_pdf.py",
      "confidence": 0.88
    }
  ]
}
```

---

## 14.5 Code Analyzer

### Responsibility

Analyze source code structure and complexity.

### Python Implementation

- Use `ast` for classes/functions/imports.
- Use `radon` for cyclomatic complexity and maintainability index.
- Use `networkx` for dependency graph.

### TypeScript/JavaScript Implementation

- Basic static parsing in v1 through file heuristics and regex.
- Future: Tree-sitter parser.

### Java Implementation

- Basic package/class/method extraction in v1.
- Future: JavaParser or Tree-sitter.

### Metrics

| Metric | Description |
|---|---|
| total_source_files | Number of source files |
| total_lines_of_code | Physical source lines |
| total_classes | Class count |
| total_functions | Function/method count |
| average_complexity | Average cyclomatic complexity |
| high_complexity_functions | Functions above threshold |
| module_count | Number of logical modules |
| dependency_edges | Number of module dependencies |

### Output

```json
{
  "metrics": {
    "total_source_files": 83,
    "total_lines_of_code": 12450,
    "total_classes": 96,
    "total_functions": 421,
    "average_complexity": 3.7,
    "high_complexity_functions": 8
  },
  "modules": [
    {
      "name": "api",
      "path": "src/grna/api",
      "classes": 4,
      "functions": 23,
      "dependencies": ["jobs", "storage"]
    }
  ]
}
```

---

## 14.6 Interface Analyzer

### Responsibility

Identify project contracts: inputs, outputs, REST APIs, CLI commands, MCP tools, config contracts, event contracts, and files produced.

### Detection Targets

| Interface Type | Detection Method |
|---|---|
| FastAPI routes | AST decorators: `@router.get`, `@router.post` |
| Flask routes | `@app.route` decorators |
| CLI commands | Typer/Click decorators |
| MCP tools | MCP server tool registration functions |
| OpenAPI | `openapi.yaml`, `swagger.json` |
| Config | `.env.example`, settings classes, YAML config |
| Events | Kafka topic constants, CloudEvents payloads |
| Artifacts | Report writer paths and MIME types |

### Output

```json
{
  "rest_apis": [
    {
      "method": "POST",
      "path": "/api/v1/release-notes/jobs",
      "input_model": "ReleaseNoteJobRequest",
      "output_model": "ReleaseNoteJobResponse",
      "source": "src/grna/api/routes_jobs.py"
    }
  ],
  "mcp_tools": [
    {
      "name": "github_release_note_submit_job",
      "input_schema": "ReleaseNoteJobRequest",
      "source": "src/grna/mcp/tools.py"
    }
  ],
  "config_contracts": [
    "GITHUB_TOKEN",
    "DATABASE_URL",
    "REDIS_URL",
    "ARTIFACT_ROOT"
  ]
}
```

---

## 14.7 Test Analyzer

### Responsibility

Detect test framework, count tests, parse test reports, and infer test scope.

### Supported Inputs

| Report | Parser |
|---|---|
| `junit.xml` | XML parser |
| `pytest-report.xml` | JUnit-compatible parser |
| `surefire-reports/*.xml` | Maven Surefire parser |
| `jest-junit.xml` | JUnit-compatible parser |
| Raw test files | Static test inventory |

### Output

```json
{
  "test_frameworks": ["pytest"],
  "test_files": 41,
  "test_cases_detected": 312,
  "test_cases_executed": 300,
  "passed": 296,
  "failed": 2,
  "skipped": 2,
  "pass_rate": 98.67,
  "warnings": []
}
```

### Behavior When Reports Are Missing

The agent should not fail the job. It should report:

```text
No machine-readable test report was found. Static test inventory was used instead.
```

---

## 14.8 Coverage Analyzer

### Responsibility

Parse available coverage artifacts and summarize code coverage.

### Supported Formats

| Format | File |
|---|---|
| Cobertura XML | `coverage.xml` |
| LCOV | `lcov.info` |
| JaCoCo XML | `jacoco.xml` |
| coverage.py DB | `.coverage` optional future support |

### Output

```json
{
  "coverage_tool": "coverage.py",
  "line_coverage_percent": 84.2,
  "branch_coverage_percent": 72.5,
  "covered_lines": 8450,
  "valid_lines": 10035,
  "low_coverage_modules": [
    {"module": "src/grna/diagrams", "coverage": 61.2}
  ]
}
```

### Missing Coverage Behavior

```text
No supported code coverage artifact was found. Coverage analytics are marked unavailable.
```

---

## 14.9 Commit Analyzer

### Responsibility

Analyze Git history for release changes.

### Inputs

- Commit history between `from_ref` and `to_ref`.
- Tags and GitHub releases if available.
- Commit messages and changed files.

### Commit Classification

| Category | Commit Patterns |
|---|---|
| Feature | `feat:`, `feature`, `add`, `implement` |
| Fix | `fix:`, `bug`, `hotfix`, `defect` |
| Docs | `docs:`, `readme`, `documentation` |
| Test | `test:`, `coverage`, `pytest`, `junit` |
| Refactor | `refactor:`, `cleanup`, `restructure` |
| Build | `build:`, `ci:`, `docker`, `helm`, `pipeline` |
| Security | `security`, `cve`, `vulnerability`, `secret` |
| Breaking | `breaking change`, `BREAKING CHANGE` |

### Output

```json
{
  "commit_range": "v2.3.9..v2.4.1",
  "total_commits": 42,
  "contributors": 5,
  "files_changed": 117,
  "insertions": 4200,
  "deletions": 1300,
  "categories": {
    "feature": 12,
    "fix": 9,
    "docs": 6,
    "test": 5,
    "refactor": 4,
    "build": 6
  },
  "breaking_changes": []
}
```

---

## 14.10 Spec Analyzer

### Responsibility

Read architecture and specification documents.

### Target Files

- `HLD.md`
- `LLD.md`
- `specs.md`
- `.kiro/specs/**/requirements.md`
- `.kiro/specs/**/design.md`
- `.kiro/specs/**/tasks.md`
- `docs/**/*.md`
- Module-local `specs.md`

### Output

```json
{
  "hld_found": true,
  "lld_found": true,
  "specs_found": 8,
  "requirements": [
    {
      "id": "REQ-001",
      "text": "The agent shall scan public GitHub repositories.",
      "source": ".kiro/specs/release-agent/requirements.md"
    }
  ],
  "architecture_decisions": [
    {
      "decision": "Use async workers for long-running repository scans.",
      "source": "docs/HLD.md"
    }
  ]
}
```

---

## 15. Diagram Generation Design

## 15.1 Mermaid Flow Diagram

Generated from analyzer pipeline and detected runtime flow.

Example:

```mermaid
flowchart LR
    GitHub[GitHub Repository] --> Clone[Clone / Fetch]
    Clone --> Inventory[File Inventory]
    Inventory --> Stack[Technology Detection]
    Inventory --> Specs[Spec Analysis]
    Stack --> Code[Code Analysis]
    Code --> Interfaces[Interface Analysis]
    Inventory --> Tests[Test Analysis]
    Inventory --> Coverage[Coverage Analysis]
    Clone --> Commits[Commit Analytics]
    Interfaces --> Report[Release Note]
    Tests --> Report
    Coverage --> Report
    Commits --> Report
```

## 15.2 C4 Context Diagram

```mermaid
C4Context
    title GitHub Release Note Intelligence Agent - Context
    Person(user, "Developer / Release Manager", "Requests professional release note generation")
    System(agent, "Release Note Intelligence Agent", "Analyzes GitHub repositories and generates release notes")
    System_Ext(github, "GitHub", "Public source repository, commits, releases")
    System_Ext(mcpClient, "MCP Client", "Codex / Kiro / Claude Code")
    System_Ext(storage, "Artifact Storage", "Generated reports and diagrams")

    Rel(user, agent, "Submits repo analysis job")
    Rel(mcpClient, agent, "Calls MCP tools")
    Rel(agent, github, "Clones repository and reads metadata")
    Rel(agent, storage, "Writes Markdown, HTML, PDF, diagrams")
```

## 15.3 C4 Container Diagram

```mermaid
C4Container
    title GitHub Release Note Intelligence Agent - Containers
    Person(user, "User")
    System_Boundary(agent, "Release Note Intelligence Agent") {
        Container(api, "REST API", "FastAPI", "Job submission and artifact download")
        Container(mcp, "MCP Server", "Python MCP", "Tool interface for agentic clients")
        Container(worker, "Async Worker", "Python", "Repo scan, analyzers, report generation")
        ContainerDb(db, "PostgreSQL", "JSONB", "Evidence model and job state")
        ContainerDb(queue, "Redis / Valkey", "Queue", "Async task queue")
        ContainerDb(artifacts, "Artifact Store", "File/S3", "Reports and diagrams")
    }
    System_Ext(github, "GitHub")

    Rel(user, api, "Submits jobs")
    Rel(api, queue, "Enqueues tasks")
    Rel(mcp, queue, "Enqueues tasks")
    Rel(worker, github, "Clones/fetches repo")
    Rel(worker, db, "Writes evidence")
    Rel(worker, artifacts, "Writes outputs")
```

## 15.4 Deployment Diagram

```mermaid
flowchart TB
    subgraph K8S[Kubernetes Namespace: release-intelligence]
        API[Deployment: release-note-api]
        MCP[Deployment: release-note-mcp]
        WORKER[Deployment: release-note-worker]
        REDIS[(Redis / Valkey)]
        PG[(PostgreSQL)]
        PVC[(Artifact PVC / Object Store)]
        ING[Ingress]
    end

    USER[User / CI / Codex] --> ING
    ING --> API
    USER --> MCP
    API --> REDIS
    MCP --> REDIS
    WORKER --> REDIS
    WORKER --> PG
    WORKER --> PVC
    WORKER --> GH[GitHub Public Repo]
```

---

## 16. Release Note Generation Design

### 16.1 Release Note Sections

1. Cover page
2. Document control and release metadata
3. Executive summary
4. Release scope
5. Project overview and intent
6. Technology and tooling summary
7. Feature summary
8. Interface/contract summary
9. Architecture diagrams
10. Deployment topology
11. Commit/change analytics
12. Code analytics
13. Test report
14. Code coverage report
15. Known issues and risks
16. Breaking changes
17. Upgrade/deployment notes
18. Rollback notes
19. Evidence appendix
20. Glossary

### 16.2 Release Note Data Model

```python
class ReleaseNoteModel(BaseModel):
    title: str
    repository: dict[str, Any]
    release_range: dict[str, Any]
    executive_summary: str
    project_intent: dict[str, Any]
    technology_summary: dict[str, Any]
    feature_summary: list[dict[str, Any]]
    interface_summary: dict[str, Any]
    architecture_diagrams: list[dict[str, Any]]
    deployment_diagrams: list[dict[str, Any]]
    commit_analytics: dict[str, Any]
    code_analytics: dict[str, Any]
    test_analytics: dict[str, Any]
    coverage_analytics: dict[str, Any]
    risks: list[dict[str, Any]]
    unknowns: list[str]
    evidence: list[EvidenceItem]
```

### 16.3 Template Rendering Flow

```mermaid
flowchart TD
    A[Evidence DB] --> B[Build ReleaseNoteModel]
    B --> C[Validate Required Sections]
    C --> D[Render Markdown via Jinja2]
    D --> E[Render HTML]
    E --> F[Render PDF]
    D --> G[Store Markdown]
    E --> H[Store HTML]
    F --> I[Store PDF]
```

---

## 17. LLM Usage Design

The agent should not rely only on LLM reasoning. It should use deterministic analyzers first, then optionally use an LLM to convert structured evidence into professional narrative.

### 17.1 LLM Allowed Tasks

- Summarize project intent from evidence.
- Rewrite feature descriptions professionally.
- Generate executive summary from structured metrics.
- Generate release-note narrative sections.
- Suggest diagram titles and captions.

### 17.2 LLM Not Allowed Tasks

- Invent missing test results.
- Invent coverage percentage.
- Invent commit history.
- Invent interfaces that were not detected.
- Hide warnings or unknowns.

### 17.3 Prompt Guardrail

```text
You are generating a professional release note using only the supplied evidence model.
Do not invent facts. If evidence is missing, write "Not available in repository evidence".
Preserve numeric metrics exactly.
Mark assumptions explicitly.
Return structured Markdown only.
```

---

## 18. Async Execution Design

### 18.1 Queue Backend

Preferred options:

1. Celery + Redis/Valkey
2. RQ + Redis
3. Arq + Redis
4. Dramatiq + Redis/RabbitMQ

Recommended for v1: **Celery + Redis/Valkey** because it is mature and easy to deploy in Kubernetes.

### 18.2 Task Breakdown

| Task | Input | Output |
|---|---|---|
| `clone_repository` | job_id, repo_url, ref | workspace path |
| `run_inventory_analysis` | job_id | inventory result |
| `run_technology_analysis` | job_id | technology result |
| `run_code_analysis` | job_id | code analytics |
| `run_interface_analysis` | job_id | interface analytics |
| `run_test_analysis` | job_id | test analytics |
| `run_coverage_analysis` | job_id | coverage analytics |
| `run_commit_analysis` | job_id | commit analytics |
| `run_spec_analysis` | job_id | spec evidence |
| `generate_diagrams` | job_id | Mermaid artifacts |
| `generate_release_note` | job_id | Markdown/HTML |
| `render_pdf` | job_id | PDF artifact |

### 18.3 Retry Policy

| Task | Retries | Retry Delay | Failure Behavior |
|---|---:|---:|---|
| Clone repository | 3 | 30s | Critical failure |
| Inventory | 1 | 10s | Critical failure |
| Technology analysis | 1 | 10s | Partial allowed |
| Code analysis | 1 | 10s | Partial allowed |
| Test analysis | 1 | 10s | Partial allowed |
| Coverage analysis | 1 | 10s | Partial allowed |
| Commit analysis | 2 | 15s | Critical if no commits found |
| Diagram generation | 1 | 10s | Partial allowed |
| PDF rendering | 2 | 15s | Markdown still available |

---

## 19. Configuration Design

### 19.1 Environment Variables

```env
GRNA_ENV=local
GRNA_API_HOST=0.0.0.0
GRNA_API_PORT=8080
GRNA_MCP_HOST=0.0.0.0
GRNA_MCP_PORT=8090

DATABASE_URL=postgresql+psycopg://grna:grna@postgresql:5432/grna
REDIS_URL=redis://redis:6379/0
ARTIFACT_ROOT=/data/artifacts
WORKSPACE_ROOT=/data/workspaces

GITHUB_TOKEN=
GITHUB_API_BASE_URL=https://api.github.com
GRNA_MAX_REPO_SIZE_MB=500
GRNA_MAX_FILE_SIZE_MB=5
GRNA_CLONE_TIMEOUT_SECONDS=600

GRNA_LLM_ENABLED=true
GRNA_LLM_PROVIDER=ollama
GRNA_OLLAMA_BASE_URL=http://ollama:11434
GRNA_OLLAMA_MODEL=llama3.2:3b

GRNA_PDF_RENDERER=weasyprint
GRNA_EXECUTE_TESTS=false
GRNA_SANDBOX_EXECUTION=false

OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
LANGFUSE_ENABLED=false
SIGNOZ_ENABLED=false
```

### 19.2 Settings Class

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8090
    database_url: str
    redis_url: str
    artifact_root: str = "/data/artifacts"
    workspace_root: str = "/data/workspaces"
    github_token: str | None = None
    max_repo_size_mb: int = 500
    max_file_size_mb: int = 5
    llm_enabled: bool = True
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"
    execute_tests: bool = False
    sandbox_execution: bool = False
```

---

## 20. Security Design

### 20.1 Safe Defaults

- Clone public repositories only in v1.
- Do not execute repository scripts by default.
- Do not read or generate secrets.
- Do not upload code outside configured storage.
- Redact tokens, passwords, keys, and `.env` values from reports.
- Limit repository size and file size.
- Use isolated workspace per job.
- Clean up workspace after retention period.

### 20.2 Dangerous Operations Blocked by Default

| Operation | Default |
|---|---|
| Run `npm install` | Blocked |
| Run `pip install -r requirements.txt` | Blocked |
| Run arbitrary test command | Blocked |
| Execute repo shell scripts | Blocked |
| Upload generated content to repo | Blocked |
| Read private repo | Blocked unless explicitly configured |

### 20.3 Secret Redaction Patterns

- `password\s*=.*`
- `token\s*=.*`
- `api[_-]?key\s*=.*`
- `secret\s*=.*`
- AWS access key patterns
- JWT-like strings
- PEM private keys

---

## 21. Observability Design

### 21.1 Logs

Every job should produce structured logs:

```json
{
  "timestamp": "2026-06-06T10:00:00Z",
  "level": "INFO",
  "job_id": "7f10fb4a-0b6e-4e65-8af4-7d3e8451fb2f",
  "component": "technology_analyzer",
  "message": "Detected FastAPI project",
  "payload": {"framework": "FastAPI"}
}
```

### 21.2 Metrics

| Metric | Type |
|---|---|
| `grna_jobs_total` | Counter |
| `grna_jobs_failed_total` | Counter |
| `grna_job_duration_seconds` | Histogram |
| `grna_repo_clone_duration_seconds` | Histogram |
| `grna_analyzer_duration_seconds` | Histogram |
| `grna_pdf_render_duration_seconds` | Histogram |
| `grna_artifact_size_bytes` | Histogram |

### 21.3 Traces

Trace spans:

- `submit_job`
- `clone_repository`
- `inventory_analysis`
- `technology_analysis`
- `code_analysis`
- `interface_analysis`
- `test_analysis`
- `coverage_analysis`
- `commit_analysis`
- `diagram_generation`
- `release_note_generation`
- `pdf_rendering`

---

## 22. PDF Rendering Design

### 22.1 Rendering Options

| Renderer | Pros | Cons |
|---|---|---|
| WeasyPrint | Good CSS support, Python-native | Mermaid rendering needs pre-step |
| Playwright Chromium | Best HTML fidelity | Heavier image/runtime |
| wkhtmltopdf | Mature | Older CSS support |
| ReportLab | Full programmatic control | More manual layout work |

Recommended v1: **HTML + Playwright** for highest visual quality, especially if Mermaid diagrams are rendered as SVG/PNG.

### 22.2 PDF Pipeline

```mermaid
flowchart LR
    MD[Markdown Release Note] --> HTML[HTML Template]
    MER[Mermaid Text] --> SVG[Mermaid SVG/PNG]
    SVG --> HTML
    HTML --> PDF[Playwright PDF]
    PDF --> STORE[Artifact Store]
```

---

## 23. Error Handling

### 23.1 Error Categories

| Error Code | Meaning | Job Impact |
|---|---|---|
| `REPO_CLONE_FAILED` | Cannot clone repo | Failed |
| `REPO_TOO_LARGE` | Repo exceeds configured size | Failed |
| `REF_NOT_FOUND` | Branch/tag/commit missing | Failed |
| `NO_SOURCE_FILES` | No source code detected | Partial/Failed based on policy |
| `NO_TEST_REPORT` | Test report missing | Partial |
| `NO_COVERAGE_REPORT` | Coverage report missing | Partial |
| `PDF_RENDER_FAILED` | PDF failed | Partial if Markdown available |
| `LLM_SUMMARY_FAILED` | LLM summary failed | Partial; deterministic summary used |
| `MCP_TOOL_ERROR` | MCP request failed | API error only |

### 23.2 Error Response

```json
{
  "error_code": "REPO_CLONE_FAILED",
  "message": "Unable to clone repository.",
  "details": {
    "repo_url": "https://github.com/example/project",
    "reason": "Repository not found or network error"
  },
  "recoverable": false
}
```

---

## 24. Testing Strategy

### 24.1 Unit Tests

| Area | Example Tests |
|---|---|
| Technology detector | Detect FastAPI from pyproject dependencies |
| Inventory analyzer | Classify test/source/spec files correctly |
| Coverage parser | Parse Cobertura XML |
| Commit analyzer | Classify conventional commits |
| Interface analyzer | Extract FastAPI route decorators |
| Report generator | Render required release-note sections |
| Secret redactor | Remove tokens/passwords from evidence |

### 24.2 Integration Tests

- Run full scan against small fixture repository.
- Generate Markdown release note.
- Generate HTML release note.
- Generate PDF release note.
- Submit job through REST API and verify artifacts.
- Submit job through MCP tool and verify artifacts.

### 24.3 Test Fixture Repositories

```text
tests/fixtures/repos/
├── python-fastapi-small/
├── node-express-small/
├── java-springboot-small/
├── mixed-k8s-helm-repo/
└── missing-coverage-repo/
```

---

## 25. Kubernetes Deployment Design

### 25.1 Kubernetes Resources

| Resource | Purpose |
|---|---|
| Deployment `release-note-api` | REST API service |
| Deployment `release-note-mcp` | MCP server service |
| Deployment `release-note-worker` | Async worker deployment |
| Service `release-note-api` | API cluster service |
| Service `release-note-mcp` | MCP service |
| ConfigMap `release-note-agent-config` | Non-secret config |
| Secret `release-note-agent-secrets` | DB credentials, GitHub token if used |
| PVC `release-note-artifacts` | Artifact storage |
| PVC `release-note-workspaces` | Temporary repo workspaces |
| Ingress `release-note-api` | External API access |
| HPA | Worker autoscaling based on queue depth/CPU |

### 25.2 Deployment Topology

```mermaid
flowchart TB
    subgraph NS[Namespace: bosgenesis or release-intelligence]
        INGRESS[Ingress]
        API_SVC[Service: release-note-api]
        MCP_SVC[Service: release-note-mcp]
        API_DEP[Deployment: release-note-api]
        MCP_DEP[Deployment: release-note-mcp]
        WORKER_DEP[Deployment: release-note-worker]
        REDIS[(Redis / Valkey)]
        POSTGRES[(PostgreSQL)]
        ART_PVC[(PVC: artifacts)]
        WORK_PVC[(PVC: workspaces)]
    end

    INGRESS --> API_SVC --> API_DEP
    MCP_SVC --> MCP_DEP
    API_DEP --> REDIS
    MCP_DEP --> REDIS
    WORKER_DEP --> REDIS
    WORKER_DEP --> POSTGRES
    WORKER_DEP --> ART_PVC
    WORKER_DEP --> WORK_PVC
    WORKER_DEP --> GITHUB[GitHub Public Repositories]
```

---

## 26. Implementation Milestones

### Phase 1: Skeleton

- FastAPI app
- MCP server skeleton
- Job table
- Artifact table
- Redis queue
- Basic clone worker
- Basic Markdown output

### Phase 2: Core Analyzers

- Inventory analyzer
- Technology detector
- Commit analyzer
- Spec analyzer
- Basic release note template

### Phase 3: Code/Test/Coverage Analytics

- Python AST analyzer
- FastAPI interface detector
- JUnit parser
- Cobertura/LCOV parser
- Analytics sections

### Phase 4: Diagrams and PDF

- Mermaid generator
- C4 generator
- Deployment diagram generator
- HTML template
- PDF renderer

### Phase 5: Enterprise Hardening

- Evidence traceability
- Secret redaction
- OpenTelemetry tracing
- Kubernetes Helm chart
- UI integration
- Retention and cleanup jobs

---

## 27. Acceptance Criteria

| ID | Criteria |
|---|---|
| AC-001 | User can submit a public GitHub repo URL and receive a job ID |
| AC-002 | Agent scans repository file tree and detects technology stack |
| AC-003 | Agent reads commit history between two refs or latest commits if refs are absent |
| AC-004 | Agent detects README, HLD, LLD, and specs.md files when present |
| AC-005 | Agent parses test report when machine-readable report exists |
| AC-006 | Agent parses coverage data when coverage artifact exists |
| AC-007 | Agent generates Mermaid flow diagrams |
| AC-008 | Agent generates C4 context/container/component diagrams |
| AC-009 | Agent generates professional Markdown release note |
| AC-010 | Agent generates professional PDF release note |
| AC-011 | Agent exposes submit/status/artifact capabilities through MCP tools |
| AC-012 | Missing coverage/test data does not fail the whole job; it is reported clearly |
| AC-013 | Generated report includes unknowns, risks, assumptions, and evidence appendix |
| AC-014 | Secrets and sensitive values are redacted from generated outputs |

---

## 28. Example Release Note Output Artifacts

```text
artifacts/{job_id}/
├── release-note.md
├── release-note.html
├── release-note.pdf
├── diagrams/
│   ├── c4-context.mmd
│   ├── c4-container.mmd
│   ├── component-diagram.mmd
│   ├── deployment-diagram.mmd
│   └── analyzer-flow.mmd
├── analytics/
│   ├── commit-analytics.json
│   ├── code-analytics.json
│   ├── coverage-analytics.json
│   ├── test-analytics.json
│   └── interface-analytics.json
└── evidence/
    └── evidence-model.json
```

---

## 29. Future Enhancements

- Private GitHub repository support through GitHub App authentication.
- Pull-request and issue analysis.
- Semantic code search using Qdrant or pgvector.
- Repository knowledge graph using Neo4j/Graphiti.
- AI-generated module-level release impact analysis.
- UI for release-note editing before PDF generation.
- Direct publishing to Confluence, GitHub Releases, SharePoint, or Jira.
- Diff-aware architecture diagram generation between releases.
- Integration with SonarQube, Codecov, Coveralls, GitHub Actions, and Jenkins.
- SBOM and dependency vulnerability summary.
- Change-risk score based on churn, test coverage, and critical modules touched.

---

## 30. Summary

This LLD defines a practical, implementation-ready Python agent for enterprise-grade release-note generation from public GitHub repositories. The design separates repository fetching, evidence extraction, analytics, diagram generation, and report rendering into modular analyzers and workers. It supports both REST and MCP interaction models, enabling usage from a UI, CI/CD pipeline, or autonomous coding agent. The final output is a professional, evidence-backed release-note package with Markdown, HTML, PDF, diagrams, analytics, and traceability artifacts.
