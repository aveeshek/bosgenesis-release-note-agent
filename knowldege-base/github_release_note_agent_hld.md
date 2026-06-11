# High-Level Design: GitHub Repository Release Note Intelligence Agent

**Document Type:** High-Level Design (HLD)  
**Proposed System Name:** `release-intelligence-agent`  
**Target Runtime:** Python, Async API Service, MCP Server-Compatible Agent  
**Primary Goal:** Analyze a public GitHub repository end-to-end and generate professional, industry-standard release notes with architecture diagrams, code analytics, test evidence, coverage summaries, interface analytics, and commit-change intelligence.

---

## 1. Executive Summary

The `release-intelligence-agent` is a Python-based autonomous analysis and documentation agent. It scans a public GitHub repository, understands the project structure, extracts engineering evidence, analyzes commit history, reads available design/specification documents, evaluates test and coverage artifacts, and generates a professional release-note package.

The agent can operate in two modes:

1. **API Mode** — called by a web application, CI/CD pipeline, or automation platform.
2. **MCP Server Mode** — exposed as an MCP-compatible tool server so external agentic systems such as Codex-like agents, Kiro-like workflows, Claude-style coding agents, or BOS Genesis orchestration layers can invoke repository-analysis tools.

The final output should be a polished release-note artifact in Markdown, HTML, and PDF formats. It should include Mermaid diagrams, C4-style architecture diagrams, deployment views, test and coverage reports, code analytics, interface analytics, and commit-change analytics.

---

## 2. Business Problem

Current release notes are often manually written, inconsistent, incomplete, and disconnected from the actual engineering evidence available in the repository. Important details such as commit history, API contracts, test coverage, architectural changes, module impact, dependency changes, and deployment topology are usually scattered across code, docs, CI artifacts, and specifications.

This creates several challenges:

- Release notes lack a professional and repeatable structure.
- Teams spend significant manual effort preparing release documentation.
- Stakeholders cannot easily understand technical impact, risk, and validation evidence.
- Architecture and deployment diagrams are often missing or outdated.
- Code coverage, test health, and commit analytics are rarely included in a usable executive format.
- Engineering evidence is not automatically traceable from repository state to release documentation.

The proposed agent solves this by creating a governed, evidence-backed release-note generation workflow.

---

## 3. Objectives

The agent must:

- Clone or read a public GitHub repository.
- Scan the complete codebase asynchronously.
- Identify technology stack, frameworks, tools, package managers, and runtime model.
- Infer project intent, features, modules, and major capabilities.
- Identify project contracts such as APIs, CLI commands, inputs, outputs, events, configuration files, and generated artifacts.
- Read full commit history and generate commit-change analytics.
- Read available code coverage reports.
- Read available unit test reports.
- Read HLD, LLD, `specs.md`, and module-level specification files.
- Analyze code structure, module relationships, interfaces, and dependencies.
- Generate Mermaid flow diagrams.
- Generate C4-style context/container/component diagrams.
- Generate deployment and runtime topology diagrams.
- Generate code analytics and interface analytics.
- Generate a professional release note in Markdown, HTML, and PDF formats.
- Expose its capabilities as API endpoints and MCP tools.
- Run long-running analysis jobs asynchronously with progress tracking.

---

## 4. Non-Objectives

The first version should not attempt to:

- Modify repository code.
- Push commits back to GitHub.
- Generate official legal/compliance sign-off.
- Replace manual release approval workflows.
- Guarantee perfect architectural understanding for every programming language.
- Execute untrusted build scripts without sandboxing.
- Read private repositories unless authentication and security design are added later.

---

## 5. Target Users

| User Type | Need |
|---|---|
| Release Manager | Generate professional release documentation quickly. |
| Tech Lead / Architect | Understand architectural changes, module impact, and technical risk. |
| QA Lead | Review test evidence, code coverage, and validation summary. |
| Developer | Understand what changed and where. |
| Product Owner | Read business-facing release highlights and feature impact. |
| Platform / DevOps Engineer | Review deployment topology, runtime dependencies, and CI/CD evidence. |
| Agentic Workflow / Codex-like Agent | Invoke repository-intelligence tools through MCP. |

---

## 6. System Context

```mermaid
flowchart LR
    User[User / Release Manager] --> UI[Web UI / CLI]
    UI --> API[Release Intelligence API]
    Agent[MCP Client / Codex-like Agent] --> MCP[MCP Server Interface]
    MCP --> API

    API --> Job[Async Job Orchestrator]
    Job --> Repo[GitHub Repository Reader]
    Job --> Analyzer[Repository Analysis Engine]
    Job --> DocGen[Release Note Generator]

    Repo --> GitHub[(Public GitHub Repo)]
    Analyzer --> Storage[(Analysis Store)]
    DocGen --> Artifacts[(Markdown / HTML / PDF / Diagrams)]
```

---

## 7. High-Level Architecture

```mermaid
flowchart TB
    subgraph ClientLayer[Client Layer]
        WebUI[Web UI]
        CLI[CLI]
        CICD[CI/CD Pipeline]
        MCPClient[MCP Client / Agent]
    end

    subgraph InterfaceLayer[Interface Layer]
        FastAPI[FastAPI REST API]
        MCPServer[MCP Server]
    end

    subgraph OrchestrationLayer[Async Orchestration Layer]
        JobManager[Job Manager]
        Queue[Task Queue]
        Workers[Async Workers]
        Progress[Progress Tracker]
    end

    subgraph AnalysisLayer[Analysis Layer]
        RepoScanner[Repository Scanner]
        TechDetector[Technology Detector]
        SpecReader[Spec and Design Reader]
        CodeAnalyzer[Code Analyzer]
        InterfaceAnalyzer[Interface Analyzer]
        TestAnalyzer[Test and Coverage Analyzer]
        CommitAnalyzer[Commit History Analyzer]
        RiskAnalyzer[Risk and Impact Analyzer]
    end

    subgraph GenerationLayer[Generation Layer]
        EvidenceModel[Evidence Model Builder]
        DiagramGenerator[Diagram Generator]
        ReleaseNoteComposer[Release Note Composer]
        PDFRenderer[PDF Renderer]
    end

    subgraph PersistenceLayer[Persistence Layer]
        MetadataDB[(PostgreSQL)]
        ObjectStore[(Artifact Storage)]
        VectorStore[(Optional Qdrant)]
        TraceStore[(MongoDB / JSONL)]
        AnalyticsDB[(Optional ClickHouse)]
    end

    WebUI --> FastAPI
    CLI --> FastAPI
    CICD --> FastAPI
    MCPClient --> MCPServer
    MCPServer --> FastAPI
    FastAPI --> JobManager
    JobManager --> Queue
    Queue --> Workers
    Workers --> AnalysisLayer
    AnalysisLayer --> EvidenceModel
    EvidenceModel --> DiagramGenerator
    EvidenceModel --> ReleaseNoteComposer
    ReleaseNoteComposer --> PDFRenderer
    GenerationLayer --> ObjectStore
    Workers --> MetadataDB
    Workers --> TraceStore
    Workers --> AnalyticsDB
    SpecReader --> VectorStore
```

---

## 8. C4 Model

### 8.1 C4 Level 1 — System Context

```mermaid
C4Context
    title System Context - Release Intelligence Agent

    Person(user, "Release Manager / Tech Lead", "Requests repository analysis and release-note generation")
    Person(agent, "External Agent", "Calls MCP tools for repo analysis and documentation generation")

    System(releaseAgent, "Release Intelligence Agent", "Analyzes GitHub repositories and generates professional release notes")
    System_Ext(github, "GitHub", "Public repository, commit history, source code, workflows, releases")
    System_Ext(ci, "CI/CD System", "Optional test reports, coverage files, build artifacts")
    System_Ext(storage, "Artifact Store", "Stores generated Markdown, HTML, PDF, diagrams, evidence JSON")

    Rel(user, releaseAgent, "Submits repo URL and generation request")
    Rel(agent, releaseAgent, "Invokes MCP tools")
    Rel(releaseAgent, github, "Clones or reads repository data")
    Rel(releaseAgent, ci, "Reads available test and coverage reports")
    Rel(releaseAgent, storage, "Publishes generated release package")
```

### 8.2 C4 Level 2 — Container Diagram

```mermaid
C4Container
    title Container Diagram - Release Intelligence Agent

    Person(user, "User", "Release manager, architect, QA lead, developer")
    System_Boundary(system, "Release Intelligence Agent") {
        Container(api, "REST API", "FastAPI", "Accepts analysis requests and returns job status/artifacts")
        Container(mcp, "MCP Server", "Python MCP SDK", "Exposes repository intelligence tools to agentic clients")
        Container(worker, "Async Worker", "Python asyncio/Celery/RQ", "Executes repository scan and analysis jobs")
        Container(analyzer, "Analysis Engine", "Python", "Detects tech stack, features, interfaces, tests, coverage, commits")
        Container(generator, "Document Generator", "Python/Jinja2/Markdown/PDF", "Generates release notes and diagrams")
        ContainerDb(db, "Metadata DB", "PostgreSQL", "Stores jobs, evidence summaries, analysis results, artifact metadata")
        ContainerDb(obj, "Artifact Store", "Filesystem/S3/MinIO", "Stores generated release-note packages")
        ContainerDb(vec, "Vector Store", "Qdrant optional", "Stores document/code chunks for semantic retrieval")
    }

    System_Ext(github, "GitHub Public Repo", "Code, commits, docs, workflows")

    Rel(user, api, "Creates analysis job")
    Rel(mcp, api, "Delegates tool execution")
    Rel(api, worker, "Queues job")
    Rel(worker, github, "Clones / fetches repository")
    Rel(worker, analyzer, "Runs analysis")
    Rel(analyzer, generator, "Sends evidence model")
    Rel(generator, obj, "Writes artifacts")
    Rel(worker, db, "Writes job status and results")
    Rel(analyzer, vec, "Indexes optional semantic chunks")
```

### 8.3 C4 Level 3 — Component Diagram

```mermaid
C4Component
    title Component Diagram - Analysis Engine

    Container_Boundary(engine, "Analysis Engine") {
        Component(repoScanner, "Repository Scanner", "Python", "Walks directory tree and classifies files")
        Component(techDetector, "Technology Detector", "Rules + heuristics", "Identifies language, framework, build tools, package managers")
        Component(intentAnalyzer, "Project Intent Analyzer", "LLM + heuristics", "Infers project purpose, users, features, and capabilities")
        Component(specReader, "Specification Reader", "Markdown parser", "Reads HLD, LLD, specs.md, module-level specs")
        Component(codeAnalyzer, "Code Analyzer", "AST/parsers", "Analyzes modules, classes, functions, complexity, imports")
        Component(interfaceAnalyzer, "Interface Analyzer", "OpenAPI/AST/config parsers", "Extracts APIs, CLI commands, events, inputs, outputs")
        Component(testAnalyzer, "Test Analyzer", "JUnit/pytest/coverage parsers", "Reads tests, failures, coverage, test evidence")
        Component(commitAnalyzer, "Commit Analyzer", "Git parser", "Reads commit history, tags, authors, changed files, release deltas")
        Component(riskAnalyzer, "Risk Analyzer", "Rules + scoring", "Calculates risk, impact, hotspots, missing evidence")
        Component(evidenceBuilder, "Evidence Model Builder", "Pydantic", "Creates normalized release evidence model")
    }

    Rel(repoScanner, techDetector, "Provides file inventory")
    Rel(repoScanner, specReader, "Provides docs list")
    Rel(repoScanner, codeAnalyzer, "Provides source files")
    Rel(repoScanner, testAnalyzer, "Provides test artifacts")
    Rel(commitAnalyzer, riskAnalyzer, "Provides change history")
    Rel(codeAnalyzer, interfaceAnalyzer, "Provides code structure")
    Rel(techDetector, evidenceBuilder, "Technology evidence")
    Rel(intentAnalyzer, evidenceBuilder, "Intent and feature evidence")
    Rel(specReader, evidenceBuilder, "Design/spec evidence")
    Rel(interfaceAnalyzer, evidenceBuilder, "Contract evidence")
    Rel(testAnalyzer, evidenceBuilder, "Test and coverage evidence")
    Rel(riskAnalyzer, evidenceBuilder, "Risk evidence")
```

---

## 9. Runtime Flow

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI API
    participant Job as Job Manager
    participant Worker as Async Worker
    participant Git as GitHub Reader
    participant Analyzer as Analysis Engine
    participant Gen as Release Note Generator
    participant Store as Artifact Store

    User->>API: POST /release-notes/jobs {repo_url, version_range, options}
    API->>Job: Create job
    Job-->>API: job_id
    API-->>User: 202 Accepted + job_id

    Job->>Worker: Dispatch async job
    Worker->>Git: Clone / fetch repository
    Git-->>Worker: Repository workspace
    Worker->>Analyzer: Scan repository
    Analyzer-->>Worker: Evidence model
    Worker->>Gen: Generate Markdown, Mermaid, HTML, PDF
    Gen->>Store: Save artifacts
    Store-->>Gen: Artifact URLs
    Worker->>Job: Mark completed

    User->>API: GET /release-notes/jobs/{job_id}
    API-->>User: Status + artifact links
```

---

## 10. Functional Modules

### 10.1 GitHub Repository Reader

Responsible for repository acquisition.

Capabilities:

- Accept public GitHub URL.
- Clone repository shallow or full depending on options.
- Fetch tags, branches, and commit history.
- Identify default branch.
- Optionally compare two tags, two branches, or latest release range.
- Read `.github/workflows` when available.
- Read release metadata if available through GitHub API.

Recommended libraries:

- `GitPython`
- `pygit2`
- `httpx`
- `PyGithub` or GitHub REST/GraphQL API

---

### 10.2 Repository Scanner

Responsible for complete file inventory and classification.

Capabilities:

- Walk repository tree.
- Exclude large/generated folders such as `.git`, `node_modules`, `target`, `build`, `.venv`, `dist`, `.mypy_cache`, `.pytest_cache`.
- Detect source files, test files, configuration files, docs, CI files, Docker files, Helm charts, Kubernetes manifests, OpenAPI files, and package files.
- Generate repository map.

Example output categories:

| Category | Examples |
|---|---|
| Source | `.py`, `.java`, `.js`, `.ts`, `.go`, `.cs` |
| Tests | `test_*.py`, `*_test.go`, `*.spec.ts`, `src/test/java` |
| Docs | `README.md`, `HLD.md`, `LLD.md`, `specs.md`, `docs/**/*.md` |
| Build | `pom.xml`, `build.gradle`, `package.json`, `pyproject.toml`, `requirements.txt` |
| CI/CD | `.github/workflows/*.yml`, `Jenkinsfile`, `.gitlab-ci.yml` |
| Deployment | `Dockerfile`, `docker-compose.yml`, `helm/**`, `k8s/**`, `manifests/**` |
| API Contracts | `openapi.yaml`, `swagger.json`, `proto`, `graphql` |

---

### 10.3 Technology and Tool Detector

Responsible for identifying technology stack and project ecosystem.

Detection sources:

- File extensions
- Package manifests
- Lock files
- Build files
- CI/CD workflows
- Dockerfiles
- Helm charts
- Kubernetes manifests
- README and docs

Example detections:

| Signal | Technology |
|---|---|
| `pyproject.toml`, `requirements.txt` | Python |
| `FastAPI`, `uvicorn` dependency | FastAPI REST service |
| `pom.xml`, `spring-boot-starter` | Java Spring Boot |
| `package.json`, `react`, `vite` | React/Vite frontend |
| `Chart.yaml`, `values.yaml` | Helm chart |
| `deployment.yaml`, `service.yaml` | Kubernetes deployment |
| `.github/workflows` | GitHub Actions CI/CD |

---

### 10.4 Project Intent and Feature Analyzer

Responsible for understanding what the project does.

Inputs:

- README files
- HLD/LLD/spec files
- Source code structure
- API routes
- CLI entrypoints
- Package metadata
- Commit messages

Outputs:

- Project purpose
- Primary users
- Key features
- Major workflows
- Inputs and outputs
- Runtime model
- Deployment model
- Operational assumptions

The agent should use a hybrid approach:

1. Deterministic extraction from docs and code.
2. LLM summarization over selected evidence chunks.
3. Confidence scoring and evidence traceability.

---

### 10.5 Specification and Design Reader

Responsible for reading formal and semi-formal design documents.

Files to detect:

- `README.md`
- `HLD.md`
- `LLD.md`
- `SPEC.md`
- `specs.md`
- `.kiro/specs/**`
- `docs/**/*.md`
- `architecture/**/*.md`
- `design/**/*.md`
- module-level `specs.md`

Outputs:

- Design summary
- Requirements summary
- Feature list
- Architecture assumptions
- Interface contracts
- Module-level behavior
- Gap list: missing HLD, missing LLD, missing specs, outdated docs

---

### 10.6 Code Analyzer

Responsible for code-level understanding.

Capabilities:

- Detect modules, packages, classes, functions, routes, commands, and dependency relationships.
- Generate module dependency graph.
- Identify code hotspots.
- Estimate complexity where possible.
- Identify public interfaces.
- Identify configuration usage.
- Identify external services and clients.
- Identify database access patterns.
- Identify security-sensitive areas.

Recommended parsing strategy:

| Language | Suggested Approach |
|---|---|
| Python | `ast`, `radon`, `libcst`, `importlib.metadata` |
| Java | `javalang`, Maven/Gradle parsing |
| JavaScript/TypeScript | tree-sitter, package manifest parsing |
| Go | `go list`, AST parsing if available |
| YAML/JSON | `ruamel.yaml`, `pydantic`, `jsonschema` |

Initial implementation can focus on Python repositories first, then expand language support.

---

### 10.7 Interface Analyzer

Responsible for extracting project contracts.

Contract types:

| Contract Type | Examples |
|---|---|
| REST API | FastAPI routes, Flask routes, Spring controllers, OpenAPI files |
| CLI | Typer, Click, argparse, shell scripts |
| MCP Tools | MCP server tool definitions |
| Events | Kafka topics, CloudEvents, queue messages |
| Files | Input/output folders, generated reports, artifact bundles |
| Configuration | `.env`, YAML config, Helm values, ConfigMaps |
| Database | Migration files, ORM models, SQL scripts |

Expected output:

- Interface inventory
- Input parameters
- Output schema
- Error responses
- Authentication hints
- External dependencies
- Contract stability score

---

### 10.8 Commit History Analyzer

Responsible for release change intelligence.

Capabilities:

- Read commits from full repository history or selected range.
- Group commits by type: feature, fix, refactor, docs, test, build, CI, security, performance.
- Detect changed files and impacted modules.
- Detect authors and contribution summary.
- Detect tags and release boundaries.
- Detect breaking-change indicators.
- Detect risky commits based on file types and critical modules.

Example analytics:

| Metric | Description |
|---|---|
| Total commits | Number of commits in selected release range |
| Files changed | Unique files changed |
| Module impact | Directory/module-level change distribution |
| Commit type mix | Feature/fix/test/docs/refactor/build ratio |
| Top contributors | Commit counts by author |
| Hotspot files | Frequently changed files |
| Risky changes | Config, deployment, auth, DB, core runtime changes |

---

### 10.9 Test and Coverage Analyzer

Responsible for validation evidence.

Files to detect:

- `coverage.xml`
- `coverage.json`
- `.coverage`
- `htmlcov/**`
- `junit.xml`
- `pytest-report.xml`
- `surefire-reports/**`
- `jacoco.xml`
- `lcov.info`
- CI-generated test artifacts when available

Outputs:

- Unit test count
- Passed/failed/skipped tests
- Test duration if available
- Coverage percentage
- Coverage by package/module if available
- Missing coverage areas
- Test evidence confidence score

If test/coverage data is not available, the release note should explicitly state:

> Test and coverage artifacts were not found in the repository. Validation evidence is unavailable from repository scan and should be provided through CI/CD integration.

---

### 10.10 Diagram Generator

Responsible for visual documentation.

Diagram types:

| Diagram | Purpose |
|---|---|
| Mermaid flow diagram | Show release generation workflow or project runtime flow |
| C4 context diagram | Show system boundary and external dependencies |
| C4 container diagram | Show major deployable units |
| C4 component diagram | Show internal modules/components |
| Deployment diagram | Show Docker/Kubernetes/Helm topology if detected |
| Module dependency graph | Show source-level module relationships |
| API/interface map | Show external contracts and consumers |
| Commit impact chart | Show changed modules and commit categories |

Deployment topology example:

```mermaid
flowchart TB
    subgraph Cluster[Kubernetes Cluster]
        subgraph NS[Application Namespace]
            Ingress[Ingress]
            Service[Service]
            Deployment[Deployment]
            Pod1[Pod Replica 1]
            Pod2[Pod Replica 2]
            ConfigMap[ConfigMap]
            Secret[Secret Reference]
            PVC[PersistentVolumeClaim]
        end
    end

    Client[External Client] --> Ingress
    Ingress --> Service
    Service --> Deployment
    Deployment --> Pod1
    Deployment --> Pod2
    Deployment --> ConfigMap
    Deployment --> Secret
    Deployment --> PVC
```

---

## 11. Release Note Output Structure

The generated release note should be professional, consistent, and evidence-backed.

Recommended structure:

1. Cover Page
2. Document Control
3. Executive Summary
4. Release Overview
5. Repository Overview
6. Technology Stack
7. Project Intent and Key Capabilities
8. Release Scope
9. Change Summary
10. Commit History Analytics
11. Codebase Analytics
12. Interface / Contract Analytics
13. Test Report Summary
14. Code Coverage Summary
15. Architecture Overview
16. C4 Context Diagram
17. C4 Container Diagram
18. C4 Component Diagram
19. Deployment Topology
20. Runtime Flow Diagrams
21. Dependency and Configuration Summary
22. Risk and Impact Assessment
23. Known Gaps / Missing Evidence
24. Upgrade / Installation Notes
25. Rollback Considerations
26. Appendix: Evidence References

---

## 12. Evidence Model

The agent should normalize all findings into an evidence model before generating documents.

Example Pydantic-style model:

```python
class ReleaseEvidence(BaseModel):
    job_id: str
    repository: RepositoryEvidence
    technology_stack: list[TechnologyEvidence]
    project_intent: ProjectIntentEvidence
    features: list[FeatureEvidence]
    interfaces: list[InterfaceEvidence]
    commits: CommitAnalyticsEvidence
    tests: TestEvidence | None
    coverage: CoverageEvidence | None
    code_analytics: CodeAnalyticsEvidence
    diagrams: list[DiagramEvidence]
    risks: list[RiskEvidence]
    gaps: list[GapEvidence]
    generated_artifacts: list[ArtifactEvidence]
```

Benefits:

- Keeps analysis separate from document rendering.
- Supports multiple output formats.
- Enables traceability from release note back to source evidence.
- Makes it easier to expose the same data through API and MCP tools.

---

## 13. API Design

### 13.1 Create Analysis Job

```http
POST /api/v1/release-notes/jobs
Content-Type: application/json
```

Request:

```json
{
  "repo_url": "https://github.com/example/project",
  "branch": "main",
  "release_from": "v1.2.0",
  "release_to": "v1.3.0",
  "output_formats": ["markdown", "html", "pdf"],
  "include_diagrams": true,
  "include_code_analytics": true,
  "include_test_analytics": true,
  "include_commit_analytics": true
}
```

Response:

```json
{
  "job_id": "rel-20260606-001",
  "status": "accepted",
  "status_url": "/api/v1/release-notes/jobs/rel-20260606-001"
}
```

### 13.2 Get Job Status

```http
GET /api/v1/release-notes/jobs/{job_id}
```

Response:

```json
{
  "job_id": "rel-20260606-001",
  "status": "running",
  "progress_percent": 62,
  "current_stage": "commit_history_analysis",
  "started_at": "2026-06-06T10:00:00Z",
  "updated_at": "2026-06-06T10:04:12Z"
}
```

### 13.3 Get Artifacts

```http
GET /api/v1/release-notes/jobs/{job_id}/artifacts
```

Response:

```json
{
  "job_id": "rel-20260606-001",
  "artifacts": [
    {
      "type": "markdown",
      "name": "release-note.md",
      "url": "/api/v1/artifacts/rel-20260606-001/release-note.md"
    },
    {
      "type": "pdf",
      "name": "release-note.pdf",
      "url": "/api/v1/artifacts/rel-20260606-001/release-note.pdf"
    }
  ]
}
```

---

## 14. MCP Server Design

The same agent should expose MCP tools so autonomous coding/documentation agents can call it.

Recommended MCP tools:

| MCP Tool | Purpose |
|---|---|
| `analyze_repository` | Start full repository analysis job. |
| `get_analysis_status` | Get async job status. |
| `get_repository_summary` | Return high-level repository summary. |
| `get_technology_stack` | Return detected technology stack. |
| `get_project_features` | Return inferred project capabilities. |
| `get_interface_inventory` | Return detected APIs, CLI, events, config contracts. |
| `get_commit_analytics` | Return commit history analytics. |
| `get_test_coverage_summary` | Return test and coverage evidence. |
| `generate_release_note` | Generate release-note artifacts from evidence. |
| `get_release_note_artifacts` | Return generated artifact links. |

Example MCP tool contract:

```json
{
  "tool_name": "analyze_repository",
  "description": "Analyze a public GitHub repository and produce normalized release evidence.",
  "input_schema": {
    "type": "object",
    "properties": {
      "repo_url": {"type": "string"},
      "branch": {"type": "string"},
      "release_from": {"type": "string"},
      "release_to": {"type": "string"},
      "include_diagrams": {"type": "boolean"}
    },
    "required": ["repo_url"]
  }
}
```

---

## 15. Async Processing Design

Repository analysis may take time, so the system should be asynchronous by design.

Recommended stages:

```mermaid
flowchart LR
    A[Job accepted] --> B[Clone repository]
    B --> C[Scan file inventory]
    C --> D[Detect technology stack]
    D --> E[Read docs and specs]
    E --> F[Analyze code]
    F --> G[Analyze interfaces]
    G --> H[Analyze tests and coverage]
    H --> I[Analyze commits]
    I --> J[Build evidence model]
    J --> K[Generate diagrams]
    K --> L[Generate release note]
    L --> M[Render PDF]
    M --> N[Publish artifacts]
```

Implementation options:

| Option | When to Use |
|---|---|
| `asyncio` + background tasks | Simple prototype, single-node deployment |
| Celery + Redis | Production-grade distributed background jobs |
| RQ + Redis | Simpler background job queue |
| Arq + Redis | Async-native Python job queue |
| Prefect / Temporal | Advanced workflow orchestration and retries |

For BOS Genesis alignment, the first practical version can use:

- FastAPI
- `asyncio`
- Redis-backed queue later
- PostgreSQL job status table
- Local filesystem or MinIO artifact storage
- Optional Langfuse/SigNoz tracing

---

## 16. Data Storage Design

### 16.1 PostgreSQL Tables

Suggested tables:

| Table | Purpose |
|---|---|
| `release_jobs` | Job metadata, status, repo URL, options |
| `repository_inventory` | File inventory and classification |
| `technology_findings` | Detected technology stack |
| `interface_findings` | API/CLI/event/config contract inventory |
| `commit_analytics` | Commit history summaries |
| `test_coverage_findings` | Test and coverage summaries |
| `release_evidence` | Normalized evidence JSON |
| `release_artifacts` | Generated artifact metadata |
| `analysis_gaps` | Missing evidence, warnings, limitations |

### 16.2 Artifact Storage

Artifacts to store:

- Markdown release note
- HTML release note
- PDF release note
- Mermaid source files
- Rendered diagram images
- Evidence JSON
- Analysis logs
- Optional repository inventory CSV/JSON

---

## 17. Security and Governance

Important controls:

- Only allow public repository URLs in v1.
- Validate GitHub URL and block local path injection.
- Clone repositories into isolated temporary workspace.
- Do not execute arbitrary repository scripts by default.
- Do not expose repository secrets if accidentally committed.
- Redact `.env`, secrets, tokens, private keys, and credential-like values.
- Limit repository size, file size, and clone depth.
- Use timeout for clone and analysis stages.
- Maintain audit trail for each job.
- Store artifact access securely.
- Clearly mark missing evidence and inferred conclusions.

Sensitive file handling:

| File Type | Default Handling |
|---|---|
| `.env` | Detect keys, redact values |
| `secret*.yaml` | Redact values |
| private keys | Do not include content |
| binary files | Inventory only |
| large files | Skip or summarize metadata only |

---

## 18. Observability

The agent should emit traceable events for each stage.

Recommended observability events:

| Event | Description |
|---|---|
| `job.accepted` | Job created |
| `repo.clone.started` | Clone started |
| `repo.clone.completed` | Clone completed |
| `scan.completed` | File inventory completed |
| `analysis.tech.completed` | Technology detection completed |
| `analysis.code.completed` | Code analysis completed |
| `analysis.tests.completed` | Test/coverage analysis completed |
| `analysis.commits.completed` | Commit analysis completed |
| `generation.diagrams.completed` | Diagrams generated |
| `generation.release_note.completed` | Release note generated |
| `job.completed` | Job finished successfully |
| `job.failed` | Job failed |

Optional BOS Genesis-aligned telemetry:

- PostgreSQL for job state and evidence
- MongoDB for raw trace documents
- ClickHouse for analytics
- Langfuse for AI/LLM traces
- SigNoz/OpenTelemetry for service traces
- Kafka for release-analysis events

---

## 19. Release Note Generation Engine

The release note generator should use templates and evidence models.

Recommended approach:

1. Build normalized evidence model.
2. Generate Mermaid diagrams from evidence.
3. Generate Markdown using Jinja2 templates.
4. Convert Markdown to HTML.
5. Render PDF using a controlled PDF engine.
6. Package all artifacts into a release bundle.

Suggested libraries:

| Need | Library Options |
|---|---|
| Markdown rendering | `markdown-it-py`, `mistune`, `python-markdown` |
| Templates | `Jinja2` |
| PDF rendering | `WeasyPrint`, `Playwright`, `ReportLab` |
| Diagrams | Mermaid CLI, Kroki, or client-side Mermaid rendering |
| Charts | matplotlib/Plotly for static charts, or SVG/HTML charts |
| Code metrics | `radon`, `lizard`, custom AST logic |
| Git history | `GitPython`, `pygit2` |

For production-grade PDF styling, HTML + CSS + Playwright/Chromium is usually the most flexible approach.

---

## 20. Generated Diagrams

The agent should produce diagram source and rendered output.

### 20.1 Project Runtime Flow

```mermaid
flowchart LR
    Client[Client / User] --> Entry[Project Entry Point]
    Entry --> Core[Core Application Logic]
    Core --> Config[Configuration]
    Core --> External[External Services]
    Core --> Output[Generated Output / API Response]
```

### 20.2 Repository Analysis Flow

```mermaid
flowchart TB
    Repo[GitHub Repository] --> Inventory[File Inventory]
    Inventory --> Tech[Technology Detection]
    Inventory --> Docs[Docs and Specs Analysis]
    Inventory --> Code[Code Analysis]
    Inventory --> Tests[Test and Coverage Analysis]
    Repo --> Commits[Commit History Analysis]
    Tech --> Evidence[Evidence Model]
    Docs --> Evidence
    Code --> Evidence
    Tests --> Evidence
    Commits --> Evidence
    Evidence --> ReleaseNote[Professional Release Note]
```

### 20.3 Release Evidence Map

```mermaid
flowchart LR
    A[README / Docs] --> E[Release Evidence Model]
    B[Source Code] --> E
    C[Commit History] --> E
    D[Test and Coverage Reports] --> E
    F[CI/CD Workflows] --> E
    G[Deployment Manifests] --> E
    E --> H[Markdown]
    E --> I[HTML]
    E --> J[PDF]
    E --> K[Diagrams]
```

---

## 21. Code Analytics

The agent should calculate and report:

| Metric | Description |
|---|---|
| Total files | Number of files scanned |
| Source files | Number of source files |
| Test files | Number of test files |
| Documentation files | Number of documentation files |
| Lines of code | Total estimated source lines |
| Comment lines | Comment density if available |
| Language distribution | Percentage by language |
| Module complexity | Cyclomatic complexity where supported |
| Dependency count | Direct and transitive dependencies if detectable |
| Hotspot modules | Modules with high change frequency or complexity |
| Dead/missing areas | Missing docs, missing tests, missing coverage |

---

## 22. Interface Analytics

The agent should produce an interface inventory table.

Example:

| Interface | Type | Input | Output | Source Evidence | Risk |
|---|---|---|---|---|---|
| `/api/v1/run` | REST API | JSON request | JSON response | FastAPI route | Medium |
| `generate-release-note` | CLI | repo URL/options | artifact path | Typer command | Low |
| `agent-events` | Kafka topic | event payload | consumer event | config/workflow | Medium |
| `settings.yaml` | Config | YAML | runtime settings | config parser | Medium |

---

## 23. Commit Change Analytics

Example release note section:

| Category | Count | Example Evidence |
|---|---:|---|
| Features | 12 | New release generation API, diagram generator |
| Fixes | 8 | PDF rendering correction, parser fallback |
| Tests | 5 | Added coverage parser tests |
| Docs | 9 | Updated README and HLD |
| CI/CD | 3 | Added GitHub Actions workflow |
| Refactor | 7 | Split analyzer modules |

Recommended charts:

- Commit category distribution
- Changed files by module
- Contributor distribution
- Timeline of commits
- Risky change summary

---

## 24. Risk and Impact Analysis

Risk scoring should consider:

| Signal | Risk Impact |
|---|---|
| Deployment files changed | High |
| Authentication/security code changed | High |
| Database migration changed | High |
| Public API contract changed | High |
| Core runtime module changed | Medium/High |
| Tests missing for changed modules | Medium/High |
| Coverage decreased | Medium |
| Docs/specs missing | Medium |
| Only documentation changed | Low |

Output should include:

- Overall release risk rating
- Top impacted modules
- Breaking-change indicators
- Missing validation evidence
- Recommended manual review areas

---

## 25. Deployment Architecture

### 25.1 Local Development

```mermaid
flowchart TB
    Dev[Developer Machine] --> API[FastAPI App]
    API --> Worker[Local Async Worker]
    API --> PG[(Local PostgreSQL)]
    Worker --> Workspace[(Temp Git Workspace)]
    Worker --> Artifacts[(Local Artifact Folder)]
```

### 25.2 Kubernetes Deployment

```mermaid
flowchart TB
    subgraph K8s[Kubernetes Cluster]
        subgraph NS[release-intelligence Namespace]
            Ingress[Ingress]
            API[release-intelligence-api Deployment]
            Worker[release-intelligence-worker Deployment]
            Redis[(Redis Queue)]
            PG[(PostgreSQL)]
            PVC[(Artifact PVC / MinIO)]
            MCP[mcp-server Service]
        end
    end

    User[User / UI] --> Ingress
    Ingress --> API
    MCPClient[MCP Client] --> MCP
    MCP --> API
    API --> Redis
    Redis --> Worker
    Worker --> PG
    Worker --> PVC
    Worker --> GitHub[GitHub Public Repo]
```

---

## 26. Suggested Repository Structure

```text
release-intelligence-agent/
├── README.md
├── pyproject.toml
├── Dockerfile
├── helm/
│   └── release-intelligence-agent/
├── src/
│   └── release_intelligence_agent/
│       ├── main.py
│       ├── api/
│       │   ├── routes_jobs.py
│       │   ├── routes_artifacts.py
│       │   └── schemas.py
│       ├── mcp/
│       │   ├── server.py
│       │   └── tools.py
│       ├── orchestration/
│       │   ├── job_manager.py
│       │   ├── queue.py
│       │   └── worker.py
│       ├── github/
│       │   ├── repo_reader.py
│       │   └── commit_reader.py
│       ├── analysis/
│       │   ├── scanner.py
│       │   ├── tech_detector.py
│       │   ├── intent_analyzer.py
│       │   ├── spec_reader.py
│       │   ├── code_analyzer.py
│       │   ├── interface_analyzer.py
│       │   ├── test_analyzer.py
│       │   ├── coverage_analyzer.py
│       │   └── risk_analyzer.py
│       ├── evidence/
│       │   ├── models.py
│       │   └── builder.py
│       ├── generation/
│       │   ├── templates/
│       │   ├── markdown_generator.py
│       │   ├── diagram_generator.py
│       │   ├── html_generator.py
│       │   └── pdf_renderer.py
│       ├── persistence/
│       │   ├── db.py
│       │   ├── repositories.py
│       │   └── artifacts.py
│       ├── observability/
│       │   ├── tracing.py
│       │   └── events.py
│       └── config.py
├── tests/
├── docs/
│   ├── HLD.md
│   ├── LLD.md
│   └── specs.md
└── examples/
```

---

## 27. Configuration

Example `.env`:

```env
RELEASE_AGENT_RUN_MODE=api
RELEASE_AGENT_API_HOST=0.0.0.0
RELEASE_AGENT_API_PORT=8080

RELEASE_AGENT_ENABLE_MCP=true
RELEASE_AGENT_MCP_HOST=0.0.0.0
RELEASE_AGENT_MCP_PORT=8081

RELEASE_AGENT_WORKSPACE_DIR=/tmp/release-intelligence/workspaces
RELEASE_AGENT_ARTIFACT_DIR=/data/release-intelligence/artifacts
RELEASE_AGENT_MAX_REPO_SIZE_MB=500
RELEASE_AGENT_MAX_FILE_SIZE_MB=5

DATABASE_URL=postgresql+psycopg://release_agent:release_agent@postgresql:5432/release_agent
REDIS_URL=redis://redis:6379/0

RELEASE_AGENT_ENABLE_QDRANT=false
QDRANT_URL=http://qdrant:6333

RELEASE_AGENT_ENABLE_LANGFUSE=false
RELEASE_AGENT_ENABLE_OTEL=false
RELEASE_AGENT_ENABLE_KAFKA_EVENTS=false
```

---

## 28. Failure Handling

| Failure | Handling |
|---|---|
| Repository clone fails | Mark job failed with GitHub access error |
| Repository too large | Stop with size-limit error |
| Unsupported language | Continue with generic file and doc analysis |
| Coverage not found | Continue and mark coverage evidence unavailable |
| Test reports not found | Continue and mark test evidence unavailable |
| Mermaid rendering fails | Include Mermaid source and mark rendered image unavailable |
| PDF rendering fails | Keep Markdown/HTML and mark PDF failed |
| LLM summarization fails | Fall back to deterministic summaries |

---

## 29. Quality Gates

Before marking the generated release note as complete, the agent should validate:

- Repository scan completed.
- Technology stack was detected or explicitly marked unknown.
- Commit history was analyzed or explicitly marked unavailable.
- Test/coverage evidence was included or marked unavailable.
- At least one architecture/runtime diagram was generated.
- Release note contains an executive summary.
- Release note contains evidence gaps and assumptions.
- Generated Markdown is valid.
- PDF artifact exists if PDF was requested.

---

## 30. Implementation Roadmap

### Phase 1 — Foundation

- FastAPI service
- Job model and status API
- Public GitHub clone
- File inventory scanner
- Basic technology detector
- Basic Markdown release-note generator

### Phase 2 — Repository Intelligence

- README/HLD/LLD/spec reader
- Commit history analyzer
- Feature and intent summarizer
- Interface detector for Python/FastAPI and CLI projects
- Evidence model

### Phase 3 — Test and Coverage Intelligence

- Coverage parser: `coverage.xml`, `lcov.info`, `jacoco.xml`
- Unit test parser: JUnit XML, pytest XML, surefire
- Test/coverage section generation
- Quality gate scoring

### Phase 4 — Diagrams and Professional PDF

- Mermaid generation
- C4 context/container/component diagrams
- Deployment topology from Docker/Helm/Kubernetes files
- HTML template
- PDF renderer
- Branded professional release-note layout

### Phase 5 — MCP Server Mode

- MCP server wrapper
- Repository analysis tools
- Artifact retrieval tools
- Async job status tools
- Integration with Codex-like or BOS Genesis agents

### Phase 6 — Production Hardening

- Redis/Celery or Arq worker backend
- PostgreSQL persistence
- Artifact store integration
- Observability with OpenTelemetry/Langfuse/SigNoz
- Security redaction
- Resource limits and sandboxing
- Kubernetes Helm chart

---

## 31. Recommended Technology Stack

| Layer | Recommendation |
|---|---|
| Language | Python 3.12+ |
| API | FastAPI |
| Async HTTP | httpx |
| Git | GitPython or pygit2 |
| Job Queue | asyncio first, Redis + Arq/Celery later |
| DB | PostgreSQL |
| Cache/Queue | Redis |
| Evidence Models | Pydantic |
| Template Engine | Jinja2 |
| Markdown | markdown-it-py or Python-Markdown |
| PDF | Playwright/Chromium or WeasyPrint |
| Diagrams | Mermaid, C4 Mermaid, optional Kroki |
| Code Metrics | radon, lizard, AST parsers |
| Testing | pytest |
| Container | Docker |
| Kubernetes | Helm chart |
| MCP | Python MCP SDK / FastMCP-style server |

---

## 32. Key Design Principle

The most important design principle is:

> The agent must not simply ask an LLM to summarize a repository. It must first build a structured evidence model from repository facts, commits, docs, tests, coverage, interfaces, and deployment files. The LLM should only help interpret and polish evidence-backed findings.

This keeps the generated release note professional, auditable, repeatable, and suitable for enterprise use.

---

## 33. Final Target Outcome

At the end of a successful job, the user should receive a release package like:

```text
release-package-{repo}-{timestamp}/
├── release-note.pdf
├── release-note.html
├── release-note.md
├── evidence.json
├── diagrams/
│   ├── c4-context.mmd
│   ├── c4-container.mmd
│   ├── c4-component.mmd
│   ├── deployment-topology.mmd
│   └── runtime-flow.mmd
├── analytics/
│   ├── code-analytics.json
│   ├── commit-analytics.json
│   ├── interface-analytics.json
│   └── test-coverage-summary.json
└── logs/
    └── analysis-trace.jsonl
```

The PDF should be suitable for leadership review, release governance, QA sign-off, customer-facing technical release documentation, and internal engineering traceability.

