from pathlib import Path

from grna.analyzers import InterfaceAnalyzer, RepositoryInventoryAnalyzer
from grna.evidence import EvidenceIndexer


def test_interface_analyzer_detects_routes_cli_mcp_env_config_and_artifacts(tmp_path) -> None:
    repo = _create_interface_fixture(tmp_path)
    inventory = RepositoryInventoryAnalyzer().analyze(repo)
    linked_inventory, _ = EvidenceIndexer("job_interface").index_inventory(inventory)

    result = InterfaceAnalyzer().analyze(repo, linked_inventory)

    assert (
        _find(result.interfaces, "http_route", "health").details["decorator"]
        == "app.get('/health')"
    )
    assert _find(result.interfaces, "cli_command", "scan").direction == "inbound"
    assert _find(result.interfaces, "mcp_tool", "release_scan").confidence == 0.9
    assert _find(result.interfaces, "environment", "GRNA_TOKEN").evidence_id
    assert _find(result.interfaces, "config", "settings.toml").direction == "internal"
    artifact = _find(result.interfaces, "artifact", "data/artifacts/{job_id}/release-note.md")
    assert artifact.direction == "outbound"
    assert result.recommendations == ()


def test_interface_analyzer_recommends_missing_contracts(tmp_path) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "plain.py").write_text("value = 1\n", encoding="utf-8")
    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    result = InterfaceAnalyzer().analyze(repo, inventory)

    assert "No explicit HTTP route contracts detected." in result.recommendations
    assert "No explicit CLI command contracts detected." in result.recommendations
    assert "No explicit MCP tool contracts detected." in result.recommendations
    assert "No environment variable interface usage detected." in result.recommendations


def _find(interfaces, interface_type: str, name: str):
    return next(
        interface
        for interface in interfaces
        if interface.interface_type == interface_type and interface.name == name
    )


def _create_interface_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    files = {
        "src/app.py": """
import os

@app.get('/health')
def health():
    return {'ok': True}

@cli.command()
def scan():
    return os.getenv('GRNA_TOKEN')

@mcp.tool()
def release_scan():
    return 'data/artifacts/{job_id}/release-note.md'
""",
        "config/settings.toml": "[app]\nname='fixture'\n",
    }
    for relative_path, content in files.items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return repo
