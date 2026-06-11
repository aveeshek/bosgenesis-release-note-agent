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

