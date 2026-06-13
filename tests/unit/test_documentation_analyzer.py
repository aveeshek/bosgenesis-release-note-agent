from pathlib import Path

from grna.analyzers import DocumentationAnalyzer, RepositoryInventoryAnalyzer
from grna.analyzers.documentation import classify_document, extract_headings, summarize_document
from grna.evidence import EvidenceIndexer


def test_documentation_analyzer_detects_docs_and_project_intent(tmp_path) -> None:
    repo = _create_documentation_fixture(tmp_path)
    (repo / "README-CN.md").write_text(
        "# Localized README\n\nLocalized project summary.\n",
        encoding="utf-8",
    )
    inventory = RepositoryInventoryAnalyzer().analyze(repo)
    linked_inventory, _ = EvidenceIndexer("job_docs").index_inventory(inventory)

    result = DocumentationAnalyzer().analyze(repo, linked_inventory)

    readme = next(document for document in result.by_kind("readme") if document.path == "README.md")
    assert readme.path == "README.md"
    assert result.by_kind("spec")[0].path == "SPEC.md"
    assert result.by_kind("hld")[0].path == "docs/HLD.md"
    assert result.by_kind("lld")[0].path == "docs/LLD.md"
    assert result.by_kind("adr")[0].path == "docs/adrs/ADR-001-records.md"
    assert result.by_kind("module_spec")[0].path == "src/grna/specs.md"

    assert readme.title == "Release Note Agent"
    assert readme.headings == ("Release Note Agent", "Usage")
    assert readme.summary.startswith("Generates evidence-backed release notes")
    assert readme.evidence_id

    assert result.project_intent.source == "stated"
    assert result.project_intent.evidence_path == "README.md"
    assert result.project_intent.text.startswith("Generates evidence-backed release notes")
    assert result.project_intent.confidence == 0.9
    assert result.gaps == ()


def test_documentation_analyzer_records_missing_spec_gaps(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text(
        "# Only README\n\nThis repo has minimal documentation.\n",
        encoding="utf-8",
    )
    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    result = DocumentationAnalyzer().analyze(repo, inventory)

    assert result.project_intent.source == "stated"
    assert "Missing SPEC documentation." in result.gaps
    assert "Missing HLD documentation." in result.gaps
    assert "Missing LLD documentation." in result.gaps
    assert "No ADR documentation detected." in result.gaps
    assert "No module-level specs.md documentation detected." in result.gaps


def test_documentation_analyzer_infers_intent_when_no_prose_summary(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Title Only\n\n- item\n", encoding="utf-8")
    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    result = DocumentationAnalyzer().analyze(repo, inventory)

    assert result.project_intent.source == "inferred"
    assert "Title Only" in result.project_intent.text
    assert result.project_intent.confidence == 0.45


def test_documentation_helpers_extract_headings_and_summaries() -> None:
    content = """
Main Title
==========

This is the first summary paragraph for the release note agent.

## Details

More detail follows.
"""

    assert extract_headings(content) == ["Main Title", "Details"]
    assert (
        summarize_document(content)
        == "This is the first summary paragraph for the release note agent."
    )
    assert classify_document("docs/adrs/ADR-001-records.md") == "adr"
    assert classify_document("src/grna/specs.md") == "module_spec"


def test_documentation_summary_skips_decorative_html() -> None:
    content = """
<img src="banner.png" />

<p align="center">
  <h1>Project</h1>
  <b>Project is an evidence-backed release-note system.</b>
</p>
"""

    assert summarize_document(content) == "Project is an evidence-backed release-note system."


def _create_documentation_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    files = {
        "README.md": """
# Release Note Agent

Generates evidence-backed release notes from public GitHub repositories.

## Usage

Run the scan command.
""",
        "SPEC.md": """
# Product Specification

Defines functional and non-functional requirements.
""",
        "docs/HLD.md": """
# High Level Design

Describes major components and runtime flow.
""",
        "docs/LLD.md": """
# Low Level Design

Describes module behavior and interfaces.
""",
        "docs/adrs/ADR-001-records.md": """
# ADR 001 Records

Records the evidence-first architecture decision.
""",
        "src/grna/specs.md": """
# GRNA Module Specification

Explains package boundaries.
""",
    }
    for relative_path, content in files.items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return repo
