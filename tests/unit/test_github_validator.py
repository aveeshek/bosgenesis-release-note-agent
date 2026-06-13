import pytest

from grna.github import GitHubUrlValidationError, validate_github_url


@pytest.mark.parametrize(
    ("raw_url", "owner", "repo"),
    [
        (
            "https://github.com/aveeshek/bosgenesis-release-note-agent",
            "aveeshek",
            "bosgenesis-release-note-agent",
        ),
        (
            "https://github.com/aveeshek/bosgenesis-release-note-agent.git",
            "aveeshek",
            "bosgenesis-release-note-agent",
        ),
        (
            "git@github.com:aveeshek/bosgenesis-release-note-agent.git",
            "aveeshek",
            "bosgenesis-release-note-agent",
        ),
        (
            "ssh://git@github.com/aveeshek/bosgenesis-release-note-agent.git",
            "aveeshek",
            "bosgenesis-release-note-agent",
        ),
        (
            "https://www.github.com/aveeshek/bosgenesis-release-note-agent",
            "aveeshek",
            "bosgenesis-release-note-agent",
        ),
    ],
)
def test_valid_github_urls_are_normalized(raw_url, owner, repo) -> None:
    parsed = validate_github_url(raw_url)

    assert parsed.owner == owner
    assert parsed.repo == repo
    assert parsed.full_name == f"{owner}/{repo}"
    assert parsed.normalized_url == f"https://github.com/{owner}/{repo}"
    assert parsed.clone_url == f"https://github.com/{owner}/{repo}.git"


def test_credentials_are_redacted_and_removed_from_clone_url() -> None:
    parsed = validate_github_url("https://token:secret@github.com/owner/repo.git")

    assert parsed.redacted_url == "https://***@github.com/owner/repo.git"
    assert parsed.clone_url == "https://github.com/owner/repo.git"
    assert "secret" not in parsed.to_dict()["redacted_url"]
    assert "token" not in parsed.clone_url


@pytest.mark.parametrize(
    ("raw_url", "error_code"),
    [
        ("", "EMPTY_URL"),
        ("/tmp/project", "LOCAL_PATH_REJECTED"),
        ("C:/tmp/project", "LOCAL_PATH_REJECTED"),
        ("file:///tmp/project", "LOCAL_PATH_REJECTED"),
        ("ftp://github.com/owner/repo", "UNSUPPORTED_URL_SCHEME"),
        ("https://gitlab.com/owner/repo", "UNSUPPORTED_GIT_HOST"),
        ("https://github.com/owner", "INVALID_GITHUB_REPOSITORY_PATH"),
        ("https://github.com/owner/repo/tree/main", "INVALID_GITHUB_REPOSITORY_PATH"),
    ],
)
def test_invalid_github_urls_return_stable_errors(raw_url, error_code) -> None:
    with pytest.raises(GitHubUrlValidationError) as exc_info:
        validate_github_url(raw_url)

    assert exc_info.value.error_code == error_code
    assert exc_info.value.to_dict()["error_code"] == error_code
