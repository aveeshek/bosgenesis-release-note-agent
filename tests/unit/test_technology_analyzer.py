from pathlib import Path

from grna.analyzers import RepositoryInventoryAnalyzer, TechnologyAnalyzer
from grna.evidence import EvidenceIndexer


def test_technology_analyzer_detects_languages_and_frameworks(tmp_path) -> None:
    repo = _create_technology_fixture(tmp_path)
    inventory = RepositoryInventoryAnalyzer().analyze(repo)
    linked_inventory, _ = EvidenceIndexer("job_tech").index_inventory(inventory)

    result = TechnologyAnalyzer().analyze(repo, linked_inventory)

    assert result.language_file_counts == {"Python": 2, "TypeScript": 1}
    assert result.find("Python").confidence == 0.95
    assert result.find("TypeScript").evidence_paths == ("web/app.ts",)
    assert result.find("FastAPI").category == "framework"
    assert result.find("MCP").category == "framework"
    assert result.find("Pydantic").category == "framework"
    assert result.find("pytest").category == "testing"
    assert result.find("Ruff").category == "linting"

    fastapi = result.find("FastAPI")
    assert fastapi.evidence_paths == ("pyproject.toml",)
    assert fastapi.evidence_ids
    assert fastapi.confidence == 0.95


def test_technology_analyzer_detects_deployment_ci_and_container_assets(tmp_path) -> None:
    repo = _create_technology_fixture(tmp_path)
    extra_workflow = repo / ".github" / "workflows" / "release.yml"
    extra_workflow.write_text("name: release\n", encoding="utf-8")
    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    result = TechnologyAnalyzer().analyze(repo, inventory)

    assert result.find("Docker").evidence_paths == ("Dockerfile",)
    assert result.find("Helm").evidence_paths == ("helm/release-note-agent/Chart.yaml",)
    assert result.find("Kubernetes").evidence_paths == ("k8s/deployment.yaml",)
    assert result.find("GitHub Actions").evidence_paths == (
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
    )
    assert all(finding.confidence > 0 for finding in result.findings)


def test_technology_analyzer_reports_unknown_when_no_language_detected(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Docs only\n", encoding="utf-8")
    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    result = TechnologyAnalyzer().analyze(repo, inventory)

    assert result.language_file_counts == {}
    unknown = result.find("Unknown language")
    assert unknown.category == "unknown"
    assert unknown.confidence == 0.2
    assert "No recognized source file extensions" in unknown.details["reason"]


def test_technology_analyzer_detects_requirements_dependencies(tmp_path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "app.py").write_text("from fastapi import FastAPI\n", encoding="utf-8")
    (repo / "requirements.txt").write_text(
        "\n".join(["fastapi==1.0.0", "pydantic>=2", "pytest", "ruff", "mcp"]),
        encoding="utf-8",
    )
    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    result = TechnologyAnalyzer().analyze(repo, inventory)

    assert result.find("Python requirements").category == "packaging"
    assert result.find("FastAPI").evidence_paths == ("requirements.txt",)
    assert result.find("MCP").confidence == 0.85


def _create_technology_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    files = {
        "pyproject.toml": """
[project]
dependencies = [
  "fastapi>=0.115",
  "pydantic>=2",
  "mcp>=1.2",
]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.5"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
""",
        "src/app.py": "from fastapi import FastAPI\n",
        "tests/test_app.py": "def test_app():\n    assert True\n",
        "web/app.ts": "export const app = 'release-note';\n",
        "Dockerfile": "FROM python:3.12-slim\n",
        ".github/workflows/ci.yml": "name: ci\n",
        "helm/release-note-agent/Chart.yaml": "apiVersion: v2\nname: release-note-agent\n",
        "k8s/deployment.yaml": "kind: Deployment\n",
    }
    for relative_path, content in files.items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return repo
