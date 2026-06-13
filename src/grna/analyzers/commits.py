"""Git commit history analyzer."""

from __future__ import annotations

import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

CommitCategory = Literal[
    "feature",
    "fix",
    "docs",
    "test",
    "refactor",
    "performance",
    "build",
    "ci",
    "chore",
    "breaking",
    "uncategorized",
]

CONVENTIONAL_CATEGORY_MAP: dict[str, CommitCategory] = {
    "feat": "feature",
    "fix": "fix",
    "docs": "docs",
    "test": "test",
    "tests": "test",
    "refactor": "refactor",
    "perf": "performance",
    "build": "build",
    "ci": "ci",
    "chore": "chore",
}

HEURISTIC_CATEGORY_KEYWORDS: tuple[tuple[str, CommitCategory], ...] = (
    ("breaking", "breaking"),
    ("add ", "feature"),
    ("introduce", "feature"),
    ("implement", "feature"),
    ("fix", "fix"),
    ("bug", "fix"),
    ("readme", "docs"),
    ("document", "docs"),
    ("test", "test"),
    ("refactor", "refactor"),
    ("performance", "performance"),
    ("speed", "performance"),
    ("docker", "build"),
    ("build", "build"),
    ("workflow", "ci"),
)


@dataclass(frozen=True, slots=True)
class CommitRecord:
    """One Git commit with changed files and assigned category."""

    sha: str
    author_name: str
    author_email: str
    authored_at: str
    subject: str
    changed_files: tuple[str, ...]
    tags: tuple[str, ...]
    category: CommitCategory
    category_source: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class Hotspot:
    """Frequently changed file or directory."""

    path: str
    change_count: int
    risk: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class CommitAnalysis:
    """Commit analyzer result."""

    commits: tuple[CommitRecord, ...]
    commit_count: int
    authors: tuple[str, ...]
    date_range: dict[str, str | None]
    changed_files: tuple[str, ...]
    category_counts: dict[str, int]
    hotspots: tuple[Hotspot, ...]
    risky_areas: tuple[Hotspot, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return {
            "commits": [commit.to_dict() for commit in self.commits],
            "commit_count": self.commit_count,
            "authors": list(self.authors),
            "date_range": self.date_range,
            "changed_files": list(self.changed_files),
            "category_counts": self.category_counts,
            "hotspots": [hotspot.to_dict() for hotspot in self.hotspots],
            "risky_areas": [area.to_dict() for area in self.risky_areas],
        }


class CommitAnalyzer:
    """Read Git commit history without executing repository code."""

    def analyze(
        self,
        repository_path: Path | str,
        from_ref: str | None = None,
        to_ref: str | None = None,
        max_commits: int = 200,
    ) -> CommitAnalysis:
        """Analyze commits in a selected range."""

        root = Path(repository_path).resolve()
        commits = self._read_commits(
            root,
            from_ref=from_ref,
            to_ref=to_ref,
            max_commits=max_commits,
        )
        authors = tuple(
            sorted({f"{commit.author_name} <{commit.author_email}>" for commit in commits})
        )
        changed_files = tuple(sorted({path for commit in commits for path in commit.changed_files}))
        dates = [commit.authored_at for commit in commits]
        category_counts = Counter(commit.category for commit in commits)
        file_counts = Counter(path for commit in commits for path in commit.changed_files)
        hotspots = tuple(
            Hotspot(path=path, change_count=count, risk=_risk_for_path(path, count))
            for path, count in file_counts.most_common(10)
        )
        risky_areas = tuple(
            hotspot for hotspot in hotspots if hotspot.risk in {"medium", "high"}
        )
        return CommitAnalysis(
            commits=tuple(commits),
            commit_count=len(commits),
            authors=authors,
            date_range={"from": min(dates) if dates else None, "to": max(dates) if dates else None},
            changed_files=changed_files,
            category_counts=dict(sorted(category_counts.items())),
            hotspots=hotspots,
            risky_areas=risky_areas,
        )

    def _read_commits(
        self,
        root: Path,
        from_ref: str | None,
        to_ref: str | None,
        max_commits: int,
    ) -> list[CommitRecord]:
        range_ref = _range_ref(from_ref, to_ref)
        command = [
            "git",
            "log",
            "--date=iso-strict",
            f"--max-count={max_commits}",
            "--pretty=format:--COMMIT--%x1f%H%x1f%an%x1f%ae%x1f%aI%x1f%s",
            "--name-only",
        ]
        if range_ref:
            command.append(range_ref)
        result = subprocess.run(command, cwd=root, capture_output=True, check=True, text=True)
        return self._parse_git_log(root, result.stdout)

    def _parse_git_log(self, root: Path, payload: str) -> list[CommitRecord]:
        commits: list[CommitRecord] = []
        current_header: list[str] | None = None
        changed_files: list[str] = []

        for line in payload.splitlines():
            if line.startswith("--COMMIT--"):
                if current_header is not None:
                    commits.append(_commit_from_parts(root, current_header, changed_files))
                current_header = _header_fields(line)
                changed_files = []
                continue
            if line.strip() and current_header is not None:
                changed_files.append(line.strip().replace("\\", "/"))

        if current_header is not None:
            commits.append(_commit_from_parts(root, current_header, changed_files))
        return commits


def categorize_commit(subject: str) -> tuple[CommitCategory, str]:
    """Categorize a commit subject without fabricating unsupported categories."""

    lowered = subject.lower()
    if "breaking change" in lowered or "!:" in lowered:
        return "breaking", "conventional"
    prefix = lowered.split(":", maxsplit=1)[0]
    prefix = prefix.split("(", maxsplit=1)[0]
    if prefix in CONVENTIONAL_CATEGORY_MAP and ":" in lowered:
        return CONVENTIONAL_CATEGORY_MAP[prefix], "conventional"
    for keyword, category in HEURISTIC_CATEGORY_KEYWORDS:
        if keyword in lowered:
            return category, "heuristic"
    return "uncategorized", "explicit"


def _header_fields(line: str) -> list[str]:
    return [
        field
        for field in line.removeprefix("--COMMIT--").split("\x1f")
        if field
    ]


def _commit_from_parts(root: Path, header: list[str], changed_files: list[str]) -> CommitRecord:
    sha, author_name, author_email, authored_at, subject = header[:5]
    category, source = categorize_commit(subject)
    return CommitRecord(
        sha=sha,
        author_name=author_name,
        author_email=author_email,
        authored_at=authored_at,
        subject=subject,
        changed_files=tuple(sorted(changed_files)),
        tags=tuple(_tags_for_commit(root, sha)),
        category=category,
        category_source=source,
    )


def _tags_for_commit(root: Path, sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "tag", "--points-at", sha],
        cwd=root,
        capture_output=True,
        check=True,
        text=True,
    )
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def _range_ref(from_ref: str | None, to_ref: str | None) -> str | None:
    if from_ref and to_ref:
        return f"{from_ref}..{to_ref}"
    return to_ref or from_ref


def _risk_for_path(path: str, count: int) -> str:
    lowered = path.lower()
    if count >= 3 or lowered.startswith(("app/config/", "src/", "k8s/", "helm/", ".github/")):
        return "high"
    if lowered.endswith((".yml", ".yaml", ".toml", ".json", ".env", "dockerfile")):
        return "medium"
    return "low"
