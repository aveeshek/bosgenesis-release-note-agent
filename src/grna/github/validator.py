"""GitHub URL validation and normalization."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import PureWindowsPath
from urllib.parse import urlparse, urlunparse

OWNER_REPO_RE = re.compile(
    r"^(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)/"
    r"(?P<repo>[A-Za-z0-9._-]+?)(?:\.git)?/?$"
)
SCP_LIKE_RE = re.compile(r"^(?P<user>git)@github\.com:(?P<path>.+)$")


class GitHubUrlValidationError(ValueError):
    """Raised when a repository URL is not a supported public GitHub URL."""

    def __init__(self, error_code: str, message: str, redacted_url: str | None = None) -> None:
        self.error_code = error_code
        self.message = message
        self.redacted_url = redacted_url
        super().__init__(message)

    def to_dict(self) -> dict[str, str | None]:
        """Return a stable error payload."""

        return {
            "error_code": self.error_code,
            "message": self.message,
            "redacted_url": self.redacted_url,
        }


@dataclass(frozen=True, slots=True)
class GitHubRepositoryUrl:
    """Normalized GitHub repository identity and safe URLs."""

    owner: str
    repo: str
    full_name: str
    normalized_url: str
    clone_url: str
    redacted_url: str
    input_url: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to JSON-compatible metadata."""

        return asdict(self)


def validate_github_url(raw_url: str) -> GitHubRepositoryUrl:
    """Validate a public GitHub repository URL and normalize owner/repo identity."""

    candidate = raw_url.strip()
    if not candidate:
        raise GitHubUrlValidationError("EMPTY_URL", "GitHub repository URL is required.")
    if _looks_like_local_path(candidate):
        raise GitHubUrlValidationError(
            "LOCAL_PATH_REJECTED",
            "Local filesystem paths are not valid GitHub repository URLs.",
            _redact_url(candidate),
        )

    scp_match = SCP_LIKE_RE.match(candidate)
    if scp_match:
        owner, repo = _parse_owner_repo_path(scp_match.group("path"), candidate)
        return _normalized_result(owner, repo, candidate, candidate)

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https", "ssh"}:
        raise GitHubUrlValidationError(
            "UNSUPPORTED_URL_SCHEME",
            f"Unsupported GitHub URL scheme: {parsed.scheme or 'none'}.",
            _redact_url(candidate),
        )

    host = (parsed.hostname or "").lower()
    if host == "www.github.com":
        host = "github.com"
    if host != "github.com":
        raise GitHubUrlValidationError(
            "UNSUPPORTED_GIT_HOST",
            "Only github.com repository URLs are supported.",
            _redact_url(candidate),
        )

    if parsed.scheme == "ssh" and parsed.username not in {"git", None}:
        raise GitHubUrlValidationError(
            "UNSUPPORTED_SSH_USER",
            "Only git@github.com SSH URLs are supported.",
            _redact_url(candidate),
        )

    owner, repo = _parse_owner_repo_path(parsed.path.lstrip("/"), candidate)
    return _normalized_result(owner, repo, candidate, _redact_url(candidate))


def _parse_owner_repo_path(path: str, raw_url: str) -> tuple[str, str]:
    match = OWNER_REPO_RE.match(path)
    if not match:
        raise GitHubUrlValidationError(
            "INVALID_GITHUB_REPOSITORY_PATH",
            "GitHub URL must point to a repository root in owner/repo form.",
            _redact_url(raw_url),
        )
    return match.group("owner"), _strip_git_suffix(match.group("repo"))


def _normalized_result(
    owner: str,
    repo: str,
    input_url: str,
    redacted_url: str,
) -> GitHubRepositoryUrl:
    full_name = f"{owner}/{repo}"
    clone_url = f"https://github.com/{full_name}.git"
    return GitHubRepositoryUrl(
        owner=owner,
        repo=repo,
        full_name=full_name,
        normalized_url=f"https://github.com/{full_name}",
        clone_url=clone_url,
        redacted_url=redacted_url,
        input_url=input_url,
    )


def _strip_git_suffix(repo: str) -> str:
    if repo.endswith(".git"):
        return repo[:-4]
    return repo


def _redact_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if not parsed.netloc or not parsed.username:
        return raw_url
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urlunparse(
        (
            parsed.scheme,
            f"***@{host}",
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def _looks_like_local_path(value: str) -> bool:
    if value.startswith(("/", "\\", "./", "../", "~")):
        return True
    if PureWindowsPath(value).drive:
        return True
    return value.lower().startswith("file:")
