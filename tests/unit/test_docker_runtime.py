from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_supports_api_runtime_dependencies() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in dockerfile
    assert "ca-certificates" in dockerfile
    assert "chromium" in dockerfile
    assert "git" in dockerfile
    assert 'python -m pip install ".[pdf]"' in dockerfile
    assert "USER grna" in dockerfile
    assert "EXPOSE 8080 8090" in dockerfile
    assert "grna.api.app:create_app" in dockerfile


def test_container_smoke_test_is_docker_only_and_uses_configurable_data_roots() -> None:
    script = (ROOT / "playbook" / "container-smoke-test.sh").read_text(encoding="utf-8")

    assert "docker build" in script
    assert "docker run -d" in script
    assert "docker compose" not in script
    assert "docker-compose" not in script
    assert "-v \"${DATA_DIR}:/data\"" in script
    assert "GRNA_WORKSPACE_ROOT=/data/workspaces" in script
    assert "GRNA_ARTIFACT_ROOT=/data/artifacts" in script
    assert "GRNA_JOB_ROOT=/data/jobs" in script
    assert "GRNA_LOG_ROOT=/data/logs" in script
    assert "${BASE_URL}/health" in script
    assert "${BASE_URL}/ready" in script
