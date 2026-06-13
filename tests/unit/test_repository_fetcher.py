import json
import subprocess
from pathlib import Path

import pytest

from grna.github import RepositoryFetcher, RepositoryFetchError
from grna.utils.paths import PathTraversalError


def _create_fixture_repo(path: Path) -> tuple[Path, str]:
    path.mkdir(parents=True)
    _git(["init"], cwd=path)
    _git(["config", "user.name", "Test User"], cwd=path)
    _git(["config", "user.email", "test@example.com"], cwd=path)
    (path / "README.md").write_text("# Fixture\n", encoding="utf-8")
    _git(["add", "README.md"], cwd=path)
    _git(["commit", "-m", "initial commit"], cwd=path)
    _git(["branch", "-M", "main"], cwd=path)
    _git(["tag", "v1.0.0"], cwd=path)
    return path, _git(["rev-parse", "HEAD"], cwd=path)


def test_fetcher_clones_local_fixture_into_job_workspace(tmp_path) -> None:
    source_repo, expected_sha = _create_fixture_repo(tmp_path / "source")
    fetcher = RepositoryFetcher(workspace_root=tmp_path / "workspaces")

    metadata = fetcher.fetch_local_fixture(source_repo, job_id="scan_001")

    repo_path = Path(metadata.repo_path)
    assert repo_path == (tmp_path / "workspaces" / "scan_001" / "repo").resolve()
    assert (repo_path / "README.md").exists()
    assert metadata.resolved_commit_sha == expected_sha
    assert metadata.default_branch == "main"
    assert metadata.selected_ref_type == "default"

    metadata_path = tmp_path / "workspaces" / "scan_001" / "fetch_metadata.json"
    saved_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert saved_metadata["resolved_commit_sha"] == expected_sha


def test_fetcher_resolves_tag_ref(tmp_path) -> None:
    source_repo, expected_sha = _create_fixture_repo(tmp_path / "source")
    fetcher = RepositoryFetcher(workspace_root=tmp_path / "workspaces")

    metadata = fetcher.fetch_local_fixture(
        source_repo,
        job_id="scan_tag",
        tag="v1.0.0",
    )

    assert metadata.selected_ref_type == "tag"
    assert metadata.selected_ref == "v1.0.0"
    assert metadata.resolved_commit_sha == expected_sha


def test_fetcher_rejects_workspace_escape(tmp_path) -> None:
    source_repo, _ = _create_fixture_repo(tmp_path / "source")
    fetcher = RepositoryFetcher(workspace_root=tmp_path / "workspaces")

    with pytest.raises(PathTraversalError):
        fetcher.fetch_local_fixture(source_repo, job_id="../escape")


def test_fetcher_rejects_existing_workspace_reuse(tmp_path) -> None:
    source_repo, _ = _create_fixture_repo(tmp_path / "source")
    fetcher = RepositoryFetcher(workspace_root=tmp_path / "workspaces")
    fetcher.fetch_local_fixture(source_repo, job_id="scan_reuse")

    with pytest.raises(RepositoryFetchError) as exc_info:
        fetcher.fetch_local_fixture(source_repo, job_id="scan_reuse")

    assert exc_info.value.error_code == "WORKSPACE_EXISTS"


def test_fetcher_returns_structured_ref_failure(tmp_path) -> None:
    source_repo, _ = _create_fixture_repo(tmp_path / "source")
    fetcher = RepositoryFetcher(workspace_root=tmp_path / "workspaces")

    with pytest.raises(RepositoryFetchError) as exc_info:
        fetcher.fetch_local_fixture(
            source_repo,
            job_id="scan_missing_ref",
            branch="does-not-exist",
        )

    assert exc_info.value.error_code == "REF_CHECKOUT_FAILED"
    assert exc_info.value.to_dict()["details"]["ref"] == "does-not-exist"


def test_fetcher_rejects_ambiguous_refs(tmp_path) -> None:
    source_repo, _ = _create_fixture_repo(tmp_path / "source")
    fetcher = RepositoryFetcher(workspace_root=tmp_path / "workspaces")

    with pytest.raises(RepositoryFetchError) as exc_info:
        fetcher.fetch_local_fixture(
            source_repo,
            job_id="scan_ambiguous",
            branch="main",
            tag="v1.0.0",
        )

    assert exc_info.value.error_code == "AMBIGUOUS_REF"


def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()
