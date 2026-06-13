from pathlib import Path

from grna.analyzers import RepositoryInventoryAnalyzer, classify_file


def test_inventory_analyzer_is_deterministic_and_detects_important_files(tmp_path) -> None:
    repo = _create_inventory_fixture(tmp_path)
    analyzer = RepositoryInventoryAnalyzer()

    first = analyzer.analyze(repo)
    second = analyzer.analyze(repo)

    assert [item.to_dict() for item in first.files] == [item.to_dict() for item in second.files]
    assert first.total_files == second.total_files
    assert first.total_size_bytes == second.total_size_bytes

    important = set(first.important_files)
    assert "README.md" in important
    assert "SPEC.md" in important
    assert "docs/HLD.md" in important
    assert "docs/LLD.md" in important
    assert "Dockerfile" in important
    assert "helm/release-note-agent/Chart.yaml" in important
    assert "coverage/coverage.xml" in important


def test_inventory_analyzer_classifies_repository_files(tmp_path) -> None:
    repo = _create_inventory_fixture(tmp_path)

    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    assert inventory.find_file("src/app.py").category == "source"
    assert inventory.find_file("tests/test_app.py").category == "test"
    assert inventory.find_file("README.md").category == "docs"
    assert inventory.find_file(".github/workflows/ci.yml").category == "ci"
    assert inventory.find_file("helm/release-note-agent/values.yaml").category == "deployment"
    assert inventory.find_file("coverage/coverage.xml").category == "coverage"
    assert inventory.find_file("image.png").category == "binary"

    assert inventory.category_counts["source"] == 1
    assert inventory.category_counts["test"] == 1
    assert inventory.category_counts["docs"] >= 4
    assert inventory.category_counts["deployment"] >= 3
    assert inventory.category_counts["coverage"] == 1


def test_inventory_analyzer_skips_generated_and_dependency_folders(tmp_path) -> None:
    repo = _create_inventory_fixture(tmp_path)

    inventory = RepositoryInventoryAnalyzer().analyze(repo)
    paths = {item.path for item in inventory.files}

    assert ".git/config" not in paths
    assert "node_modules/left-pad/index.js" not in paths
    assert ".venv/pyvenv.cfg" not in paths
    assert "build/generated.js" not in paths
    assert "__pycache__/app.pyc" not in paths
    assert set(inventory.skipped_directories) >= {
        ".git",
        ".venv",
        "__pycache__",
        "build",
        "node_modules",
    }


def test_classify_file_without_filesystem_access() -> None:
    assert classify_file("Dockerfile") == "deployment"
    assert classify_file(".github/workflows/build.yml") == "ci"
    assert classify_file("coverage/lcov.info") == "coverage"
    assert classify_file("src/service.ts") == "source"


def _create_inventory_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    files = {
        "README.md": "# Release Note Agent\n",
        "SPEC.md": "# Spec\n",
        "docs/HLD.md": "# HLD\n",
        "docs/LLD.md": "# LLD\n",
        "Dockerfile": "FROM python:3.12-slim\n",
        "src/app.py": "print('hello')\n",
        "tests/test_app.py": "def test_app():\n    assert True\n",
        ".github/workflows/ci.yml": "name: ci\n",
        "helm/release-note-agent/Chart.yaml": "apiVersion: v2\nname: release-note-agent\n",
        "helm/release-note-agent/values.yaml": "replicaCount: 1\n",
        "k8s/deployment.yaml": "kind: Deployment\n",
        "coverage/coverage.xml": "<coverage />\n",
        "config/settings.toml": "[tool]\n",
        ".git/config": "[core]\n",
        "node_modules/left-pad/index.js": "module.exports = function() {}\n",
        ".venv/pyvenv.cfg": "home = /tmp\n",
        "build/generated.js": "console.log('generated')\n",
        "__pycache__/app.pyc": "compiled\n",
    }
    for relative_path, content in files.items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    binary_path = repo / "image.png"
    binary_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00")
    return repo
