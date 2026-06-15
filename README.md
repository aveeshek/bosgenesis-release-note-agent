# GitHub Release Note Intelligence Agent

Python agent for scanning public GitHub repositories and generating evidence-backed, human-readable release-note packages in Markdown, HTML, and PDF.

The project follows the `SPEC -> PLAN -> Tasks -> Code` workflow captured in `knowldege-base/`, `tasks.md`, and module-level `specs.md` files.

## Current Status

The repository is in foundation development. The package skeleton, module specs, report style contract, task plan, configuration module, and structured logging module are in place.

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Common Commands

```powershell
python -m pytest
python -m ruff check .
python -c "import grna; print(grna.__version__)"
```

## Local Storage

The MVP storage layer uses local files so development can proceed without a database:

- Job status: `data/jobs/{job_id}.json`
- Generated artifacts: `data/artifacts/{job_id}/...`
- Artifact manifest: `data/artifacts/{job_id}/artifacts.json`

Storage callers use interfaces in `grna.storage.interfaces` so PostgreSQL-backed job and artifact metadata persistence can replace the JSON store later without changing analyzer or report code.

## API and MCP Development Servers

```powershell
python -m uvicorn grna.api.app:create_app --factory --host 0.0.0.0 --port 8080
python -m uvicorn grna.mcp.server:create_mcp_app --factory --host 0.0.0.0 --port 8090
```

The MCP server exposes Streamable HTTP MCP at `/mcp` and a compatibility HTTP
surface for curl smoke tests:

- `GET /mcp/tools`
- `POST /mcp/tools/github_release_scan_start`
- `POST /mcp/tools/github_release_scan_status`
- `POST /mcp/tools/github_release_get_analytics`
- `POST /mcp/tools/github_release_generate_note`
- `POST /mcp/tools/github_release_get_artifact`
- `POST /mcp/tools/github_release_list_evidence`
- `POST /mcp/tools/github_release_get_diagrams`
- `POST /mcp/tools/github_release_note_submit_job`
- `POST /mcp/tools/github_release_note_get_job_status`
- `POST /mcp/tools/github_release_note_list_artifacts`
- `POST /mcp/tools/github_release_note_get_artifact`
- `POST /mcp/tools/github_release_note_get_evidence`
- `POST /mcp/tools/github_release_note_cancel_job`
- `POST /mcp/tools/github_repo_scan_only`
- `POST /mcp/tools/github_commit_analytics_only`
- `POST /mcp/tools/github_code_analytics_only`
- `POST /mcp/tools/scan_github_repository`
- `POST /mcp/tools/get_release_note_job_status`
- `POST /mcp/tools/get_repository_analysis_summary`
- `POST /mcp/tools/generate_release_note`
- `POST /mcp/tools/get_release_note_artifact`
- `POST /mcp/tools/get_release_note_artifacts`

## Local Docker Runtime

Docker Compose is intentionally not part of this project. The local container
runtime is a single Docker image for the API process; Kubernetes/Helm remains
the deployment path for multi-process environments.

Build the image:

```bash
docker build -t bosgenesis-release-note-agent:local .
```

Run the API container with configurable local storage roots:

```bash
mkdir -p data/container-local/{workspaces,artifacts,jobs,logs}
docker run --rm \
  --name bosgenesis-release-note-agent-local \
  -p 8080:8080 \
  -v "$(pwd)/data/container-local:/data" \
  -e GRNA_WORKSPACE_ROOT=/data/workspaces \
  -e GRNA_ARTIFACT_ROOT=/data/artifacts \
  -e GRNA_JOB_ROOT=/data/jobs \
  -e GRNA_LOG_ROOT=/data/logs \
  bosgenesis-release-note-agent:local
```

Smoke-test the local container:

```bash
./playbook/container-smoke-test.sh
```

## Helm Deployment

```bash
RELEASE_NAME=bosgenesis-release-note-agent NAMESPACE=bosgenesis ./playbook/deploy.sh
RELEASE_NAME=bosgenesis-release-note-agent NAMESPACE=bosgenesis ./playbook/undeploy.sh
```

The Helm chart deploys REST API and MCP services by default. The worker deployment is included but disabled until the async worker implementation is added.

## Runtime Configuration

Copy `.env.example` to `.env` for local development once environment loading is implemented. Current configuration defaults are read directly from environment variables by `grna.config`.

## Design Sources

- `knowldege-base/SPEC.md`
- `knowldege-base/PLAN.md`
- `docs/report-style-spec.md`
- `src/grna/**/specs.md`
- `tasks.md`

## Safety Principle

Scanned repositories are untrusted input. The agent must not execute repository code, install dependencies from scanned repositories, or expose secrets found in repository content by default.
