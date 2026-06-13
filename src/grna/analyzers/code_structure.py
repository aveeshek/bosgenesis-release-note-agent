"""Python code structure analyzer."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from grna.analyzers.inventory import RepositoryInventory

EntrypointKind = Literal["python_main", "console_script", "fastapi_app", "cli_app"]


@dataclass(frozen=True, slots=True)
class PythonModuleSummary:
    """Parsed Python module structure."""

    path: str
    module_name: str
    loc: int
    classes: tuple[str, ...]
    functions: tuple[str, ...]
    imports: tuple[str, ...]
    public_surfaces: tuple[str, ...]
    entrypoints: tuple[str, ...]
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class DirectorySummary:
    """Directory-level source summary."""

    path: str
    file_count: int
    loc: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class Entrypoint:
    """Detected executable/public entrypoint."""

    kind: EntrypointKind
    name: str
    path: str
    confidence: float
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class CodeStructureAnalysis:
    """Code structure analyzer result."""

    modules: tuple[PythonModuleSummary, ...]
    directories: tuple[DirectorySummary, ...]
    entrypoints: tuple[Entrypoint, ...]
    gaps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return {
            "modules": [module.to_dict() for module in self.modules],
            "directories": [directory.to_dict() for directory in self.directories],
            "entrypoints": [entrypoint.to_dict() for entrypoint in self.entrypoints],
            "gaps": list(self.gaps),
        }


class CodeStructureAnalyzer:
    """Parse Python files with `ast` and report partial gaps for other languages."""

    def analyze(
        self,
        repository_path: Path | str,
        inventory: RepositoryInventory,
    ) -> CodeStructureAnalysis:
        """Return module inventory, directory summary, entrypoints, and gaps."""

        root = Path(repository_path).resolve()
        modules: list[PythonModuleSummary] = []
        entrypoints: list[Entrypoint] = []
        unsupported_extensions: set[str] = set()

        for file in inventory.files:
            suffix = Path(file.path).suffix.lower()
            if suffix == ".py":
                module = _parse_python_module(root, file.path, file.evidence_id)
                modules.append(module)
                entrypoints.extend(_entrypoints_for_module(module))
            elif file.category == "source":
                unsupported_extensions.add(suffix or "<none>")

        modules.sort(key=lambda item: item.path)
        entrypoints.sort(key=lambda item: (item.path, item.kind, item.name))
        directories = _directory_summaries(modules)
        gaps = tuple(
            f"Unsupported source extension for structure parsing: {extension}"
            for extension in sorted(unsupported_extensions)
        )
        return CodeStructureAnalysis(
            modules=tuple(modules),
            directories=directories,
            entrypoints=tuple(entrypoints),
            gaps=gaps,
        )


def _parse_python_module(
    root: Path,
    relative_path: str,
    evidence_id: str | None,
) -> PythonModuleSummary:
    path = root / relative_path
    content = path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=relative_path)
    classes: list[str] = []
    functions: list[str] = []
    imports: set[str] = set()
    entrypoint_markers: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            if _has_cli_decorator(node):
                entrypoint_markers.add(f"cli:{node.name}")
        elif isinstance(node, ast.Import):
            imports.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", maxsplit=1)[0])
        elif _is_python_main_guard(node):
            entrypoint_markers.add("__main__")
        elif _is_fastapi_app_assignment(node):
            entrypoint_markers.add("fastapi_app")

    public_surfaces = tuple(
        sorted(name for name in [*classes, *functions] if not name.startswith("_"))
    )
    return PythonModuleSummary(
        path=relative_path,
        module_name=_module_name(relative_path),
        loc=sum(1 for line in content.splitlines() if line.strip()),
        classes=tuple(sorted(classes)),
        functions=tuple(sorted(functions)),
        imports=tuple(sorted(imports)),
        public_surfaces=public_surfaces,
        entrypoints=tuple(sorted(entrypoint_markers)),
        evidence_id=evidence_id,
    )


def _directory_summaries(modules: list[PythonModuleSummary]) -> tuple[DirectorySummary, ...]:
    buckets: dict[str, list[PythonModuleSummary]] = {}
    for module in modules:
        directory = str(Path(module.path).parent).replace("\\", "/")
        if directory == ".":
            directory = ""
        buckets.setdefault(directory, []).append(module)
    return tuple(
        DirectorySummary(
            path=directory,
            file_count=len(items),
            loc=sum(item.loc for item in items),
        )
        for directory, items in sorted(buckets.items())
    )


def _entrypoints_for_module(module: PythonModuleSummary) -> list[Entrypoint]:
    entrypoints: list[Entrypoint] = []
    for marker in module.entrypoints:
        if marker == "__main__":
            entrypoints.append(_entrypoint("python_main", "__main__", module))
        elif marker == "fastapi_app":
            entrypoints.append(_entrypoint("fastapi_app", "FastAPI app", module))
        elif marker.startswith("cli:"):
            entrypoints.append(_entrypoint("cli_app", marker.removeprefix("cli:"), module))
    return entrypoints


def _entrypoint(kind: EntrypointKind, name: str, module: PythonModuleSummary) -> Entrypoint:
    return Entrypoint(
        kind=kind,
        name=name,
        path=module.path,
        confidence=0.9,
        evidence_id=module.evidence_id,
    )


def _has_cli_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        text = ast.unparse(decorator).lower()
        if ".command" in text or ".callback" in text or "typer" in text:
            return True
    return False


def _is_python_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    return ast.unparse(node.test).replace(" ", "") == "__name__=='__main__'"


def _is_fastapi_app_assignment(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign):
        return False
    return "FastAPI(" in ast.unparse(node.value)


def _module_name(relative_path: str) -> str:
    path = Path(relative_path)
    without_suffix = path.with_suffix("")
    return ".".join(part for part in without_suffix.parts if part != "__init__")
