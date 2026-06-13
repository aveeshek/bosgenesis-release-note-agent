import subprocess
from pathlib import Path

from grna.analyzers import CommitAnalyzer
from grna.analyzers.commits import categorize_commit


def test_commit_analyzer_reports_history_authors_dates_files_and_tags(tmp_path) -> None:
    repo = _create_git_fixture(tmp_path)

    result = CommitAnalyzer().analyze(repo)

    assert result.commit_count == 5
    assert result.authors == ("Test User <test@example.com>",)
    assert result.date_range["from"] <= result.date_range["to"]
    assert "src/app.py" in result.changed_files
    assert "README.md" in result.changed_files
    assert result.category_counts["feature"] == 1
    assert result.category_counts["fix"] == 1
    assert result.category_counts["docs"] == 1
    assert result.category_counts["uncategorized"] == 2

    tagged = next(commit for commit in result.commits if "v1.0.0" in commit.tags)
    assert tagged.subject == "feat: add app module"
    assert tagged.category_source == "conventional"
    assert result.hotspots[0].change_count >= 1
    assert any(area.path == "src/app.py" for area in result.risky_areas)


def test_commit_analyzer_supports_selected_range(tmp_path) -> None:
    repo = _create_git_fixture(tmp_path)
    first = _git(["rev-list", "--max-parents=0", "HEAD"], cwd=repo)

    result = CommitAnalyzer().analyze(repo, from_ref=first, to_ref="HEAD")

    assert result.commit_count == 4
    assert all(commit.subject != "initial commit" for commit in result.commits)


def test_categorize_commit_keeps_uncategorized_explicit() -> None:
    assert categorize_commit("misc updates") == ("uncategorized", "explicit")
    assert categorize_commit("fix: repair login") == ("fix", "conventional")
    assert categorize_commit("improve performance of worker") == ("performance", "heuristic")


def _create_git_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], cwd=repo)
    _git(["config", "user.name", "Test User"], cwd=repo)
    _git(["config", "user.email", "test@example.com"], cwd=repo)

    _write(repo / "README.md", "# Fixture\n")
    _commit(repo, "initial commit")

    _write(repo / "src" / "app.py", "def app():\n    return 'ok'\n")
    _commit(repo, "feat: add app module")
    _git(["tag", "v1.0.0"], cwd=repo)

    _write(repo / "src" / "app.py", "def app():\n    return 'fixed'\n")
    _commit(repo, "fix: repair app module")

    _write(repo / "README.md", "# Fixture\n\nDocs.\n")
    _commit(repo, "docs: update readme")

    _write(repo / "notes.txt", "misc\n")
    _commit(repo, "misc updates")
    return repo


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit(repo: Path, message: str) -> None:
    _git(["add", "."], cwd=repo)
    _git(["commit", "-m", message], cwd=repo)


def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True, text=True)
    return result.stdout.strip()
