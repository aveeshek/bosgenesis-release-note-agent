"""Specification and documentation analyzer."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from grna.analyzers.inventory import InventoryFile, RepositoryInventory

DocumentKind = Literal["readme", "spec", "hld", "lld", "adr", "module_spec", "docs", "other"]
IntentSource = Literal["stated", "inferred", "unavailable"]

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TITLE_UNDERLINE_PATTERN = re.compile(r"^[-=]{3,}\s*$")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
REQUIRED_DOC_KINDS = ("readme", "spec", "hld", "lld")


@dataclass(frozen=True, slots=True)
class DocumentSummary:
    """One detected documentation file."""

    path: str
    kind: DocumentKind
    title: str | None
    headings: tuple[str, ...]
    summary: str
    evidence_path: str
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProjectIntent:
    """Project intent extracted or inferred from documentation."""

    text: str
    source: IntentSource
    evidence_path: str | None = None
    evidence_id: str | None = None
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class DocumentationInventory:
    """Documentation analyzer result."""

    documents: tuple[DocumentSummary, ...]
    project_intent: ProjectIntent
    gaps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return {
            "documents": [document.to_dict() for document in self.documents],
            "project_intent": self.project_intent.to_dict(),
            "gaps": list(self.gaps),
        }

    def by_kind(self, kind: DocumentKind) -> tuple[DocumentSummary, ...]:
        """Return detected documents by kind."""

        return tuple(document for document in self.documents if document.kind == kind)


class DocumentationAnalyzer:
    """Detect docs, extract headings/summaries, intent, and missing documentation gaps."""

    def analyze(
        self,
        repository_path: Path | str,
        inventory: RepositoryInventory,
    ) -> DocumentationInventory:
        """Return deterministic documentation inventory."""

        root = Path(repository_path).resolve()
        documents = [
            self._summarize_document(root, file)
            for file in inventory.files
            if _is_documentation_file(file)
        ]
        documents = [document for document in documents if document is not None]
        documents.sort(key=lambda item: item.path)

        gaps = _documentation_gaps(documents)
        intent = _detect_project_intent(documents)
        return DocumentationInventory(
            documents=tuple(documents),
            project_intent=intent,
            gaps=tuple(gaps),
        )

    def _summarize_document(self, root: Path, file: InventoryFile) -> DocumentSummary | None:
        path = root / file.path
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

        headings = extract_headings(content)
        title = headings[0] if headings else _fallback_title(file.path)
        return DocumentSummary(
            path=file.path,
            kind=classify_document(file.path),
            title=title,
            headings=tuple(headings),
            summary=summarize_document(content),
            evidence_path=file.path,
            evidence_id=file.evidence_id,
        )


def classify_document(relative_path: str) -> DocumentKind:
    """Classify documentation path into the documentation inventory taxonomy."""

    normalized = relative_path.replace("\\", "/").lower()
    filename = normalized.rsplit("/", maxsplit=1)[-1]
    if filename.startswith("readme"):
        return "readme"
    if filename == "spec.md" or filename == "spec":
        return "spec"
    if filename == "hld.md" or filename == "hld":
        return "hld"
    if filename == "lld.md" or filename == "lld":
        return "lld"
    if filename.startswith("adr-") or "/adr/" in normalized or "/adrs/" in normalized:
        return "adr"
    if filename == "specs.md":
        return "module_spec"
    if normalized.startswith("docs/") or "/docs/" in normalized:
        return "docs"
    return "other"


def extract_headings(content: str) -> list[str]:
    """Extract Markdown/RST-like headings in source order."""

    lines = content.splitlines()
    headings: list[str] = []
    for index, line in enumerate(lines):
        markdown_match = HEADING_PATTERN.match(line)
        if markdown_match:
            headings.append(markdown_match.group(2).strip())
            continue
        if index > 0 and TITLE_UNDERLINE_PATTERN.match(line):
            previous = lines[index - 1].strip()
            if previous:
                headings.append(previous)
    return headings


def summarize_document(content: str, max_chars: int = 220) -> str:
    """Return a concise factual summary from the first meaningful prose block."""

    paragraphs = _prose_paragraphs(content)
    if not paragraphs:
        return "No prose summary available."
    summary = paragraphs[0]
    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 3].rstrip() + "..."


def _is_documentation_file(file: InventoryFile) -> bool:
    return file.category == "docs" or classify_document(file.path) in {
        "readme",
        "spec",
        "hld",
        "lld",
        "adr",
        "module_spec",
        "docs",
    }


def _documentation_gaps(documents: list[DocumentSummary]) -> list[str]:
    present = {document.kind for document in documents}
    gaps = [
        f"Missing {kind.upper()} documentation."
        for kind in REQUIRED_DOC_KINDS
        if kind not in present
    ]
    if "adr" not in present:
        gaps.append("No ADR documentation detected.")
    if "module_spec" not in present:
        gaps.append("No module-level specs.md documentation detected.")
    return gaps


def _detect_project_intent(documents: list[DocumentSummary]) -> ProjectIntent:
    priority_documents = [
        *[document for document in documents if document.path.casefold() == "readme.md"],
        *[document for document in documents if document.kind == "spec"],
        *[document for document in documents if document.kind == "readme"],
    ]
    for document in priority_documents:
        if document.summary != "No prose summary available.":
            return ProjectIntent(
                text=document.summary,
                source="stated",
                evidence_path=document.evidence_path,
                evidence_id=document.evidence_id,
                confidence=0.9 if document.kind == "readme" else 0.85,
            )
    for document in documents:
        if document.title:
            return ProjectIntent(
                text=f"Project intent inferred from documentation title: {document.title}.",
                source="inferred",
                evidence_path=document.evidence_path,
                evidence_id=document.evidence_id,
                confidence=0.45,
            )
    return ProjectIntent(
        text="Project intent unavailable because no readable documentation was detected.",
        source="unavailable",
        confidence=0.0,
    )


def _prose_paragraphs(content: str) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    lines = content.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            _flush_paragraph(current, paragraphs)
            continue
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if next_line and TITLE_UNDERLINE_PATTERN.match(next_line):
            _flush_paragraph(current, paragraphs)
            continue
        if stripped.startswith(("#", "```", "|", "-", "*", ">")):
            _flush_paragraph(current, paragraphs)
            continue
        if _is_decorative_html_line(stripped):
            _flush_paragraph(current, paragraphs)
            continue
        if TITLE_UNDERLINE_PATTERN.match(stripped):
            _flush_paragraph(current, paragraphs)
            continue
        cleaned = _clean_prose_line(stripped)
        if cleaned:
            current.append(cleaned)
    _flush_paragraph(current, paragraphs)
    return paragraphs


def _flush_paragraph(current: list[str], paragraphs: list[str]) -> None:
    if current:
        paragraphs.append(" ".join(current))
        current.clear()


def _fallback_title(relative_path: str) -> str:
    return Path(relative_path).stem.replace("-", " ").replace("_", " ").title()


def _is_decorative_html_line(line: str) -> bool:
    lower = line.lower()
    return (
        lower.startswith("<img")
        or lower.startswith("<br")
        or lower.startswith("<p")
        or lower.startswith("</p")
        or bool(re.match(r"<h[1-6][\s>]", lower))
    )


def _clean_prose_line(line: str) -> str:
    return HTML_TAG_PATTERN.sub("", line).strip()
