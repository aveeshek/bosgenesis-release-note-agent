"""Safe repository fetching into isolated workspaces."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from grna.config import AppConfig, get_config
from grna.storage.models import utc_now_iso
from grna.utils.paths import ensure_directory, safe_join

from .validator import GitHubRepositoryUrl, validate_github_url

RefType = Literal["branch", "tag", "commit", "default"]


class RepositoryFetchError(RuntimeError):
    """Raised when a repository cannot be fetched safely."""

    def __init__(
        self,
        error_code: str,
        message: str,
        details: dict[str, str] | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        """Return a stable structured error payload."""

        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class FetchMetadata:
    """Repository fetch metadata recorded beside each job workspace."""

    job_id: str
    source_url: str
    redacted_url: str
    normalized_url: str | None
    owner: str | None
    repo: str | None
    repo_path: str
    workspace_path: str
    default_branch: str | None
    selected_ref_type: RefType
    selected_ref: str | None
    resolved_commit_sha: str
    fetched_at: str

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible metadata."""

        return asdict(self)


class RepositoryFetcher:
    """Clone public GitHub repositories into root-bound job workspaces."""

    METADATA_FILE = "fetch_metadata.json"

    def __init__(
        self,
        workspace_root: Path | str | None = None,
        config: AppConfig | None = None,
    ) -> None:
        resolved_config = config or get_config()
        self.workspace_root = ensure_directory(workspace_root or resolved_config.workspace_root)

    def fetch_public_repository(
        self,
        repo_url: str,
        job_id: str,
        branch: str | None = None,
        tag: str | None = None,
        commit_sha: str | None = None,
    ) -> FetchMetadata:
        """Validate and clone a public GitHub repository."""

        validated = validate_github_url(repo_url)
        return self._fetch(
            clone_source=validated.clone_url,
            source_url=validated.normalized_url,
            redacted_url=validated.redacted_url,
            job_id=job_id,
            branch=branch,
            tag=tag,
            commit_sha=commit_sha,
            repository_url=validated,
        )

    def fetch_local_fixture(
        self,
        fixture_repo: Path | str,
        job_id: str,
        branch: str | None = None,
        tag: str | None = None,
        commit_sha: str | None = None,
    ) -> FetchMetadata:
        """Clone a local Git fixture for tests without weakening URL validation."""

        source = Path(fixture_repo).expanduser().resolve()
        return self._fetch(
            clone_source=str(source),
            source_url=str(source),
            redacted_url=str(source),
            job_id=job_id,
            branch=branch,
            tag=tag,
            commit_sha=commit_sha,
            repository_url=None,
        )

    def _fetch(
        self,
        clone_source: str,
        source_url: str,
        redacted_url: str,
        job_id: str,
        branch: str | None,
        tag: str | None,
        commit_sha: str | None,
        repository_url: GitHubRepositoryUrl | None,
    ) -> FetchMetadata:
        ref_type, selected_ref = _resolve_requested_ref(branch, tag, commit_sha)
        workspace_path = safe_join(self.workspace_root, job_id)
        repo_path = safe_join(workspace_path, "repo")
        template_path = safe_join(workspace_path, "empty-git-template")
        if repo_path.exists() and any(repo_path.iterdir()):
            raise RepositoryFetchError(
                "WORKSPACE_EXISTS",
                "Job repository workspace already exists and will not be reused.",
                {"job_id": job_id, "repo_path": str(repo_path)},
            )

        workspace_path.mkdir(parents=True, exist_ok=True)
        template_path.mkdir(parents=True, exist_ok=True)

        try:
            git_env = {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_LFS_SKIP_SMUDGE": "1",
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_TEMPLATE_DIR": str(template_path),
            }
            _run_git(
                [
                    "clone",
                    "--no-recurse-submodules",
                    clone_source,
                    str(repo_path),
                ],
                env=git_env,
            )
            default_branch = _detect_default_branch(repo_path)
            self._checkout_ref(repo_path, ref_type, selected_ref)
            metadata = FetchMetadata(
                job_id=job_id,
                source_url=source_url,
                redacted_url=redacted_url,
                normalized_url=repository_url.normalized_url if repository_url else None,
                owner=repository_url.owner if repository_url else None,
                repo=repository_url.repo if repository_url else None,
                repo_path=str(repo_path),
                workspace_path=str(workspace_path),
                default_branch=default_branch,
                selected_ref_type=ref_type,
                selected_ref=selected_ref,
                resolved_commit_sha=_run_git(["rev-parse", "HEAD"], cwd=repo_path).strip(),
                fetched_at=utc_now_iso(),
            )
            self._write_metadata(workspace_path, metadata)
            shutil.rmtree(template_path, ignore_errors=True)
            return metadata
        except RepositoryFetchError:
            shutil.rmtree(repo_path, ignore_errors=True)
            raise
        except GitCommandFailure as exc:
            shutil.rmtree(repo_path, ignore_errors=True)
            raise RepositoryFetchError(
                "FETCH_FAILED",
                "Repository fetch failed.",
                {"source_url": redacted_url, "reason": _safe_git_error(exc)},
            ) from exc

    def _checkout_ref(self, repo_path: Path, ref_type: RefType, selected_ref: str | None) -> None:
        if ref_type == "default" or selected_ref is None:
            return
        try:
            if ref_type == "tag":
                _run_git(["checkout", f"tags/{selected_ref}"], cwd=repo_path)
            else:
                _run_git(["checkout", selected_ref], cwd=repo_path)
        except GitCommandFailure as exc:
            raise RepositoryFetchError(
                "REF_CHECKOUT_FAILED",
                "Repository was cloned but requested ref could not be checked out.",
                {"ref_type": ref_type, "ref": selected_ref, "reason": _safe_git_error(exc)},
            ) from exc

    def _write_metadata(self, workspace_path: Path, metadata: FetchMetadata) -> None:
        metadata_path = safe_join(workspace_path, self.METADATA_FILE)
        metadata_path.write_text(
            json.dumps(metadata.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )


def _resolve_requested_ref(
    branch: str | None,
    tag: str | None,
    commit_sha: str | None,
) -> tuple[RefType, str | None]:
    requested = {
        "branch": branch,
        "tag": tag,
        "commit": commit_sha,
    }
    present = [(key, value) for key, value in requested.items() if value]
    if len(present) > 1:
        raise RepositoryFetchError(
            "AMBIGUOUS_REF",
            "Specify only one of branch, tag, or commit_sha.",
            {"requested": ",".join(key for key, _ in present)},
        )
    if not present:
        return "default", None
    ref_type, selected_ref = present[0]
    return ref_type, selected_ref


class GitCommandFailure(RuntimeError):
    """Internal wrapper for failed git commands."""

    def __init__(self, args: list[str], returncode: int, stdout: str, stderr: str) -> None:
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(stderr or stdout or f"git exited with {returncode}")


def _run_git(
    args: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise GitCommandFailure(args, result.returncode, result.stdout, result.stderr)
    return result.stdout.strip()


def _detect_default_branch(repo_path: Path) -> str | None:
    try:
        remote_head = _run_git(
            ["symbolic-ref", "refs/remotes/origin/HEAD", "--short"],
            cwd=repo_path,
        )
        if remote_head.startswith("origin/"):
            return remote_head.removeprefix("origin/")
        return remote_head or None
    except GitCommandFailure:
        branch = _run_git(["branch", "--show-current"], cwd=repo_path)
        return branch or None


def _safe_git_error(exc: GitCommandFailure) -> str:
    stderr = (exc.stderr or "").strip()
    stdout = (exc.stdout or "").strip()
    return stderr or stdout or str(exc.returncode) or "git command failed"
