from pathlib import Path

from grna.analyzers import CodeStructureAnalyzer, RepositoryInventoryAnalyzer
from grna.evidence import EvidenceIndexer


def test_code_structure_analyzer_builds_python_module_inventory(tmp_path) -> None:
    repo = _create_code_fixture(tmp_path)
    inventory = RepositoryInventoryAnalyzer().analyze(repo)
    linked_inventory, _ = EvidenceIndexer("job_code").index_inventory(inventory)

    result = CodeStructureAnalyzer().analyze(repo, linked_inventory)

    service = next(module for module in result.modules if module.path == "src/app/service.py")
    assert service.module_name == "src.app.service"
    assert service.classes == ("Service",)
    assert service.functions == ("_private", "create_app", "main")
    assert service.imports == ("os", "typer")
    assert service.public_surfaces == ("Service", "create_app", "main")
    assert service.evidence_id

    assert any(
        directory.path == "src/app" and directory.file_count == 2
        for directory in result.directories
    )
    assert any(entry.kind == "python_main" for entry in result.entrypoints)
    assert any(entry.kind == "cli_app" and entry.name == "main" for entry in result.entrypoints)


def test_code_structure_analyzer_identifies_fastapi_entrypoint_and_partial_gaps(tmp_path) -> None:
    repo = _create_code_fixture(tmp_path)
    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    result = CodeStructureAnalyzer().analyze(repo, inventory)

    assert any(
        entry.kind == "fastapi_app" and entry.path == "src/app/api.py"
        for entry in result.entrypoints
    )
    assert "Unsupported source extension for structure parsing: .ts" in result.gaps


def _create_code_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    files = {
        "src/app/service.py": """
import os
import typer

class Service:
    pass

def create_app():
    return Service()

def _private():
    return None

@typer_app.command()
def main():
    print(os.getenv("APP_ENV"))

if __name__ == "__main__":
    main()
""",
        "src/app/api.py": """
from fastapi import FastAPI

app = FastAPI()
""",
        "web/index.ts": "export const value = 1;\n",
    }
    for relative_path, content in files.items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return repo
