"""Technology inventory analyzer."""

from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from grna.analyzers.inventory import InventoryFile, RepositoryInventory

TechnologyCategory = Literal[
    "language",
    "packaging",
    "framework",
    "testing",
    "linting",
    "container",
    "deployment",
    "ci",
    "unknown",
]


LANGUAGE_BY_EXTENSION = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".mjs": "JavaScript",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sh": "Shell",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
}


@dataclass(frozen=True, slots=True)
class TechnologyFinding:
    """Detected technology with traceable evidence."""

    name: str
    category: TechnologyCategory
    confidence: float
    evidence_paths: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class TechnologyInventory:
    """Technology analyzer result."""

    findings: tuple[TechnologyFinding, ...]
    unknowns: tuple[TechnologyFinding, ...]
    language_file_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return {
            "findings": [finding.to_dict() for finding in self.findings],
            "unknowns": [finding.to_dict() for finding in self.unknowns],
            "language_file_counts": self.language_file_counts,
        }

    def find(self, name: str) -> TechnologyFinding | None:
        """Return a finding by case-insensitive name."""

        normalized = name.casefold()
        for finding in (*self.findings, *self.unknowns):
            if finding.name.casefold() == normalized:
                return finding
        return None


class TechnologyAnalyzer:
    """Detect languages, manifests, frameworks, tooling, and deployment assets."""

    def analyze(
        self,
        repository_path: Path | str,
        inventory: RepositoryInventory,
    ) -> TechnologyInventory:
        """Return deterministic technology findings from inventory and manifest files."""

        root = Path(repository_path).resolve()
        findings: list[TechnologyFinding] = []
        unknowns: list[TechnologyFinding] = []

        language_counts = self._detect_languages(inventory, findings)
        self._detect_python_packaging(root, inventory, findings)
        self._detect_python_dependencies(root, inventory, findings)
        self._detect_file_based_technologies(inventory, findings)

        if not language_counts:
            unknowns.append(
                TechnologyFinding(
                    name="Unknown language",
                    category="unknown",
                    confidence=0.2,
                    evidence_paths=(),
                    details={"reason": "No recognized source file extensions were found."},
                )
            )

        findings = _merge_findings(findings)
        findings.sort(key=lambda item: (item.category, item.name))
        unknowns.sort(key=lambda item: item.name)
        return TechnologyInventory(
            findings=tuple(findings),
            unknowns=tuple(unknowns),
            language_file_counts=dict(sorted(language_counts.items())),
        )

    def _detect_languages(
        self,
        inventory: RepositoryInventory,
        findings: list[TechnologyFinding],
    ) -> dict[str, int]:
        paths_by_language: dict[str, list[InventoryFile]] = {}
        for file in inventory.files:
            suffix = Path(file.path).suffix.lower()
            language = LANGUAGE_BY_EXTENSION.get(suffix)
            if language is None:
                continue
            paths_by_language.setdefault(language, []).append(file)

        for language, files in sorted(paths_by_language.items()):
            findings.append(
                TechnologyFinding(
                    name=language,
                    category="language",
                    confidence=0.95,
                    evidence_paths=tuple(file.path for file in files[:10]),
                    evidence_ids=tuple(file.evidence_id for file in files[:10] if file.evidence_id),
                    details={"file_count": len(files)},
                )
            )
        return {language: len(files) for language, files in paths_by_language.items()}

    def _detect_python_packaging(
        self,
        root: Path,
        inventory: RepositoryInventory,
        findings: list[TechnologyFinding],
    ) -> None:
        pyproject = inventory.find_file("pyproject.toml")
        requirements = inventory.find_file("requirements.txt")
        if pyproject is not None:
            findings.append(_finding("Python packaging", "packaging", pyproject, 0.95))
            self._detect_pyproject_tools(root / pyproject.path, pyproject, findings)
        if requirements is not None:
            findings.append(_finding("Python requirements", "packaging", requirements, 0.9))

    def _detect_pyproject_tools(
        self,
        pyproject_path: Path,
        file: InventoryFile,
        findings: list[TechnologyFinding],
    ) -> None:
        try:
            payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
            return

        dependencies = _lower_join(payload.get("project", {}).get("dependencies", []))
        optional = payload.get("project", {}).get("optional-dependencies", {})
        optional_dependencies = _lower_join(
            dependency for values in optional.values() for dependency in values
        )
        build_system = payload.get("build-system", {})
        tool_config = payload.get("tool", {})
        combined = " ".join(
            [dependencies, optional_dependencies, _lower_join(build_system.values())]
        )

        if "fastapi" in combined:
            findings.append(_finding("FastAPI", "framework", file, 0.95))
        if "mcp" in combined:
            findings.append(_finding("MCP", "framework", file, 0.9))
        if "pydantic" in combined:
            findings.append(_finding("Pydantic", "framework", file, 0.95))
        if "pytest" in combined or "pytest" in tool_config:
            findings.append(_finding("pytest", "testing", file, 0.95))
        if "ruff" in combined or "ruff" in tool_config:
            findings.append(_finding("Ruff", "linting", file, 0.95))

    def _detect_python_dependencies(
        self,
        root: Path,
        inventory: RepositoryInventory,
        findings: list[TechnologyFinding],
    ) -> None:
        requirements = inventory.find_file("requirements.txt")
        if requirements is None:
            return
        try:
            content = (root / requirements.path).read_text(encoding="utf-8").lower()
        except (OSError, UnicodeDecodeError):
            return

        dependency_map = {
            "fastapi": ("FastAPI", "framework", 0.9),
            "mcp": ("MCP", "framework", 0.85),
            "pydantic": ("Pydantic", "framework", 0.9),
            "pytest": ("pytest", "testing", 0.9),
            "ruff": ("Ruff", "linting", 0.9),
        }
        for marker, (name, category, confidence) in dependency_map.items():
            if marker in content:
                findings.append(_finding(name, category, requirements, confidence))

    def _detect_file_based_technologies(
        self,
        inventory: RepositoryInventory,
        findings: list[TechnologyFinding],
    ) -> None:
        for file in inventory.files:
            normalized = file.path.lower()
            filename = normalized.rsplit("/", maxsplit=1)[-1]
            if filename == "dockerfile" or filename.startswith("dockerfile."):
                findings.append(_finding("Docker", "container", file, 0.95))
            if normalized.startswith(".github/workflows/"):
                findings.append(_finding("GitHub Actions", "ci", file, 0.95))
            if normalized.startswith(("helm/", "charts/")) and filename == "chart.yaml":
                findings.append(_finding("Helm", "deployment", file, 0.95))
            if normalized.startswith(("k8s/", "kubernetes/")) or filename in {
                "deployment.yaml",
                "deployment.yml",
                "service.yaml",
                "service.yml",
                "ingress.yaml",
                "ingress.yml",
            }:
                findings.append(_finding("Kubernetes", "deployment", file, 0.9))


def _finding(
    name: str,
    category: TechnologyCategory,
    file: InventoryFile,
    confidence: float,
) -> TechnologyFinding:
    return TechnologyFinding(
        name=name,
        category=category,
        confidence=confidence,
        evidence_paths=(file.path,),
        evidence_ids=(file.evidence_id,) if file.evidence_id else (),
    )


def _lower_join(values: Any) -> str:
    if isinstance(values, str):
        return values.lower()
    if isinstance(values, dict):
        values = values.values()
    try:
        return " ".join(str(value).lower() for value in values)
    except TypeError:
        return str(values).lower()


def _merge_findings(findings: list[TechnologyFinding]) -> list[TechnologyFinding]:
    merged: dict[tuple[str, TechnologyCategory], TechnologyFinding] = {}
    for finding in findings:
        key = (finding.name, finding.category)
        existing = merged.get(key)
        if existing is None:
            merged[key] = finding
            continue
        evidence_paths = tuple(dict.fromkeys([*existing.evidence_paths, *finding.evidence_paths]))
        evidence_ids = tuple(dict.fromkeys([*existing.evidence_ids, *finding.evidence_ids]))
        details = existing.details
        if details is None and finding.details is not None:
            details = finding.details
        merged[key] = TechnologyFinding(
            name=existing.name,
            category=existing.category,
            confidence=max(existing.confidence, finding.confidence),
            evidence_paths=evidence_paths,
            evidence_ids=evidence_ids,
            details=details,
        )
    return list(merged.values())
