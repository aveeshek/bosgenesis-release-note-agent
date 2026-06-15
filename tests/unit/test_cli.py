import json
import subprocess
from pathlib import Path

from grna.cli.main import main
from grna.config import reset_config_cache


def test_cli_scan_status_and_generate_note(tmp_path, monkeypatch, capsys) -> None:
    _configure_roots(tmp_path, monkeypatch)
    source_repo = _create_fixture_repo(tmp_path / "source")

    exit_code = main(
        [
            "scan",
            "https://github.com/example/fixture",
            "--local-repo",
            str(source_repo),
            "--format",
            "markdown",
            "--format",
            "html",
            "--json",
        ],
    )

    assert exit_code == 0
    scan_payload = json.loads(capsys.readouterr().out)
    assert scan_payload["status"] == "completed"
    assert scan_payload["progress_percent"] == 100
    artifact_types = {artifact["artifact_type"] for artifact in scan_payload["artifacts"]}
    expected_artifacts = {"analytics", "evidence", "metadata", "markdown", "html", "observability"}
    assert expected_artifacts <= artifact_types
    observability = json.loads(_artifact_path(scan_payload, "observability").read_text())
    assert observability["schema_version"] == "phase13.observability.v1"
    assert observability["trace_ids"]["signoz"] is None
    assert observability["sinks"]["structured_audit"] == "enabled"
    assert observability["sinks"]["phase_latency_metrics"] == "enabled"
    assert observability["audit_event_count"] == len(observability["audit_events"])
    phase_names = {item["phase"] for item in observability["phase_metrics"]}
    assert {"fetching_repository", "indexing_evidence", "generating_release_note"}.issubset(
        phase_names
    )
    assert any(
        item["event_type"] == "artifact_generated"
        for item in observability["audit_events"]
    )

    exit_code = main(["status", scan_payload["job_id"], "--json"])

    assert exit_code == 0
    status_payload = json.loads(capsys.readouterr().out)
    assert status_payload["job"]["status"] == "completed"
    assert len(status_payload["artifacts"]) == len(scan_payload["artifacts"])

    analytics_path = _artifact_path(scan_payload, "analytics")
    generated_dir = tmp_path / "generated"
    exit_code = main(
        [
            "generate-note",
            str(analytics_path),
            "--output-dir",
            str(generated_dir),
            "--title",
            "Fixture Release Notes",
            "--release-name",
            "v1.0.0",
            "--repository",
            "https://github.com/example/fixture",
            "--format",
            "markdown",
            "--format",
            "html",
            "--json",
        ],
    )

    assert exit_code == 0
    generated_payload = json.loads(capsys.readouterr().out)
    assert sorted(Path(path).name for path in generated_payload["files"]) == [
        "release-note.html",
        "release-note.md",
    ]
    assert (generated_dir / "release-note.html").exists()
    assert (generated_dir / "release-note.md").exists()


def test_cli_returns_useful_json_error_for_missing_job(tmp_path, monkeypatch, capsys) -> None:
    _configure_roots(tmp_path, monkeypatch)

    exit_code = main(["status", "scan_missing", "--json"])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().err)
    assert payload["error_code"] == "JOB_NOT_FOUND"
    assert "scan_missing" in payload["message"]


def _configure_roots(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GRNA_JOB_ROOT", str(tmp_path / "jobs"))
    monkeypatch.setenv("GRNA_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("GRNA_WORKSPACE_ROOT", str(tmp_path / "workspaces"))
    reset_config_cache()


def _create_fixture_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(["init"], cwd=path)
    _git(["config", "user.name", "Test User"], cwd=path)
    _git(["config", "user.email", "test@example.com"], cwd=path)
    (path / "README.md").write_text(
        "# Fixture\n\nA small FastAPI service used by CLI tests.\n",
        encoding="utf-8",
    )
    (path / "pyproject.toml").write_text(
        "[project]\nname = \"fixture\"\nversion = \"1.0.0\"\n"
        "dependencies = [\"fastapi\", \"pydantic\"]\n",
        encoding="utf-8",
    )
    source = path / "src" / "fixture"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text("", encoding="utf-8")
    (source / "app.py").write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/health')\n"
        "def health():\n    return {'ok': True}\n",
        encoding="utf-8",
    )
    tests = path / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    _git(["add", "."], cwd=path)
    _git(["commit", "-m", "feat: initial fixture"], cwd=path)
    _git(["branch", "-M", "main"], cwd=path)
    _git(["tag", "v1.0.0"], cwd=path)
    return path


def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _artifact_path(scan_payload: dict, artifact_type: str) -> Path:
    for artifact in scan_payload["artifacts"]:
        if artifact["artifact_type"] == artifact_type:
            return Path(artifact["path"])
    raise AssertionError(f"Missing artifact type: {artifact_type}")
