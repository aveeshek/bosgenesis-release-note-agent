"""Repository inventory analyzer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Literal

from grna.utils.hashing import sha256_file

FileCategory = Literal[
    "source",
    "test",
    "docs",
    "config",
    "ci",
    "deployment",
    "coverage",
    "binary",
    "other",
]


SKIPPED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".tox",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".cache",
        "node_modules",
        "bower_components",
        "dist",
        "build",
        "target",
        ".next",
        ".nuxt",
        ".parcel-cache",
        ".turbo",
        ".gradle",
        "htmlcov",
    }
)

SOURCE_EXTENSIONS = frozenset(
    {
        ".c",
        ".cc",
        ".cpp",
        ".cs",
        ".go",
        ".java",
        ".js",
        ".jsx",
        ".kt",
        ".mjs",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".scala",
        ".sh",
        ".ts",
        ".tsx",
    }
)
DOC_EXTENSIONS = frozenset({".adoc", ".md", ".rst", ".txt"})
CONFIG_EXTENSIONS = frozenset(
    {".cfg", ".conf", ".env", ".ini", ".json", ".toml", ".xml", ".yaml", ".yml"}
)
BINARY_EXTENSIONS = frozenset(
    {
        ".7z",
        ".bin",
        ".class",
        ".dll",
        ".doc",
        ".docx",
        ".exe",
        ".gif",
        ".gz",
        ".ico",
        ".jar",
        ".jpg",
        ".jpeg",
        ".pdf",
        ".png",
        ".pyc",
        ".so",
        ".tar",
        ".war",
        ".zip",
    }
)
COVERAGE_FILENAMES = frozenset(
    {
        ".coverage",
        "clover.xml",
        "coverage-final.json",
        "coverage.json",
        "coverage.xml",
        "jacoco.xml",
        "lcov.info",
        "cobertura.xml",
    }
)
IMPORTANT_FILENAMES = frozenset(
    {
        "readme",
        "readme.md",
        "readme.rst",
        "spec",
        "spec.md",
        "hld",
        "hld.md",
        "lld",
        "lld.md",
        "dockerfile",
        "chart.yaml",
        "values.yaml",
        "coverage.xml",
        "lcov.info",
    }
)


@dataclass(frozen=True, slots=True)
class InventoryFile:
    """Normalized file metadata from a repository inventory pass."""

    path: str
    category: FileCategory
    size_bytes: int
    checksum_sha256: str
    important: bool = False
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)

    def with_evidence(self, evidence_id: str) -> InventoryFile:
        """Return this file record linked to an evidence item."""

        return replace(self, evidence_id=evidence_id)


@dataclass(frozen=True, slots=True)
class RepositoryInventory:
    """Deterministic repository inventory result."""

    root_path: str
    files: tuple[InventoryFile, ...]
    total_files: int
    total_size_bytes: int
    category_counts: dict[str, int]
    skipped_directories: tuple[str, ...]
    important_files: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        payload = asdict(self)
        payload["files"] = [file.to_dict() for file in self.files]
        return payload

    def find_file(self, relative_path: str) -> InventoryFile | None:
        """Return a file by repository-relative path."""

        normalized = relative_path.replace("\\", "/")
        for file in self.files:
            if file.path == normalized:
                return file
        return None


class RepositoryInventoryAnalyzer:
    """Walk a repository tree and classify files without executing repository code."""

    def analyze(self, repository_path: Path | str) -> RepositoryInventory:
        """Return a deterministic inventory for a repository path."""

        root = Path(repository_path).resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"repository path is not a directory: {root}")

        files: list[InventoryFile] = []
        skipped_directories: set[str] = set()

        self._walk(root, root, files, skipped_directories)
        files.sort(key=lambda item: item.path)

        category_counts = {category: 0 for category in FileCategory.__args__}  # type: ignore[attr-defined]
        for item in files:
            category_counts[item.category] += 1

        return RepositoryInventory(
            root_path=str(root),
            files=tuple(files),
            total_files=len(files),
            total_size_bytes=sum(item.size_bytes for item in files),
            category_counts=category_counts,
            skipped_directories=tuple(sorted(skipped_directories)),
            important_files=tuple(item.path for item in files if item.important),
        )

    def _walk(
        self,
        root: Path,
        current: Path,
        files: list[InventoryFile],
        skipped_directories: set[str],
    ) -> None:
        children = sorted(current.iterdir(), key=lambda item: item.name.lower())
        for child in children:
            relative_path = child.relative_to(root).as_posix()
            if child.is_dir():
                if _should_skip_directory(child.name):
                    skipped_directories.add(relative_path)
                    continue
                self._walk(root, child, files, skipped_directories)
                continue

            if child.is_file():
                category = classify_file(relative_path, child)
                files.append(
                    InventoryFile(
                        path=relative_path,
                        category=category,
                        size_bytes=child.stat().st_size,
                        checksum_sha256=sha256_file(child),
                        important=is_important_file(relative_path, category),
                    )
                )


def classify_file(relative_path: str, absolute_path: Path | None = None) -> FileCategory:
    """Classify a repository-relative path into a release-note inventory category."""

    normalized = relative_path.replace("\\", "/")
    path_parts = tuple(part.lower() for part in normalized.split("/"))
    filename = path_parts[-1]
    suffix = Path(filename).suffix.lower()

    if filename in COVERAGE_FILENAMES or "coverage" in path_parts[:-1]:
        return "coverage"
    if absolute_path is not None and is_binary_file(absolute_path):
        return "binary"
    if suffix in BINARY_EXTENSIONS:
        return "binary"
    if len(path_parts) >= 3 and path_parts[0] == ".github" and path_parts[1] == "workflows":
        return "ci"
    if path_parts[0] in {"helm", "charts", "k8s", "kubernetes", "deploy", "deployment"}:
        return "deployment"
    if filename in {"dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
        return "deployment"
    if (
        "test" in path_parts
        or "tests" in path_parts
        or filename.startswith("test_")
        or filename.endswith("_test.py")
    ):
        return "test"
    if (
        filename in {"readme.md", "readme.rst", "spec.md", "hld.md", "lld.md"}
        or suffix in DOC_EXTENSIONS
    ):
        return "docs"
    if suffix in CONFIG_EXTENSIONS or filename in {"makefile", ".gitignore", ".dockerignore"}:
        return "config"
    if suffix in SOURCE_EXTENSIONS:
        return "source"
    return "other"


def is_important_file(relative_path: str, category: FileCategory) -> bool:
    """Return whether a file deserves first-class evidence and report attention."""

    normalized = relative_path.replace("\\", "/").lower()
    filename = normalized.rsplit("/", maxsplit=1)[-1]
    if filename in IMPORTANT_FILENAMES:
        return True
    if filename in COVERAGE_FILENAMES:
        return True
    if category == "deployment" and ("helm/" in normalized or "/helm/" in normalized):
        return True
    return normalized.endswith(("/spec.md", "/hld.md", "/lld.md"))


def is_binary_file(path: Path, sample_size: int = 4096) -> bool:
    """Return a conservative binary-file guess without loading large files."""

    with path.open("rb") as file_handle:
        sample = file_handle.read(sample_size)
    if b"\x00" in sample:
        return True
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def _should_skip_directory(name: str) -> bool:
    return name.lower() in SKIPPED_DIRECTORY_NAMES
