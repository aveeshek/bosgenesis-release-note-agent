from grna.diagrams import MermaidDiagramGenerator
from grna.evidence import AnalyticsBundle, AnalyticsSection, EvidenceIndex, EvidenceRecord
from grna.reports import MarkdownReleaseNoteRenderer, ReleaseNoteContent


def test_markdown_release_note_contains_required_sections_and_diagrams() -> None:
    content = _content()

    markdown = MarkdownReleaseNoteRenderer().render(content)

    for section in [
        "# Release Note",
        "## Document Control",
        "## Executive Summary",
        "## Release Overview",
        "## Repository Overview",
        "## Project Intent",
        "## Technology Inventory",
        "## Architecture Overview",
        "## Interface Inventory",
        "## Code Analytics",
        "## Test Analytics",
        "## Coverage Analytics",
        "## Commit Analytics",
        "## Quality and Risk Assessment",
        "## Known Gaps",
        "## Evidence Traceability",
        "## Appendix",
    ]:
        assert section in markdown
    assert "```mermaid" in markdown
    assert "### Repository Analysis Flow" in markdown
    assert "| Python | language | 0.95 | `ev_py` |" in markdown


def test_markdown_release_note_includes_evidence_appendix_and_missing_statements() -> None:
    content = _content()

    markdown = MarkdownReleaseNoteRenderer().render(content)

    assert "| `ev_doc` | README.md | README evidence |" in markdown
    assert "- No coverage report evidence detected." in markdown
    assert "Coverage evidence is missing; no coverage percentage is reported." in markdown


def test_markdown_release_note_handles_missing_evidence_index() -> None:
    content = _content(include_evidence=False)

    markdown = MarkdownReleaseNoteRenderer().render(content)

    assert "| `ev_doc` | Not available | Evidence metadata not available. |" in markdown


def _content(include_evidence: bool = True) -> ReleaseNoteContent:
    bundle = AnalyticsBundle(
        job_id="job_report",
        generated_at="2026-06-13T00:00:00+00:00",
        sections={
            "documentation": AnalyticsSection(
                name="documentation",
                data={
                    "project_intent": {
                        "text": "Generates release notes from repository evidence.",
                        "source": "stated",
                        "evidence_id": "ev_doc",
                    }
                },
                evidence_ids=("ev_doc",),
            ),
            "technology": AnalyticsSection(
                name="technology",
                data={
                    "findings": [
                        {
                            "name": "Python",
                            "category": "language",
                            "confidence": 0.95,
                            "evidence_ids": ["ev_py"],
                        }
                    ]
                },
                evidence_ids=("ev_py",),
            ),
            "test_coverage": AnalyticsSection(
                name="test_coverage",
                data={"test_sources": [{"path": "tests/test_app.py"}], "coverage_reports": []},
                gaps=("No coverage report evidence detected.",),
                evidence_ids=("ev_test",),
            ),
            "commits": AnalyticsSection(
                name="commits",
                data={
                    "commit_count": 2,
                    "authors": ["A <a@example.com>"],
                    "changed_files": ["src/app.py"],
                    "risky_areas": [{"path": "src/app.py"}],
                },
            ),
        },
        gaps=("No coverage report evidence detected.",),
        warnings=(),
        evidence_ids=("ev_doc", "ev_py", "ev_test"),
    )
    diagrams = MermaidDiagramGenerator().generate(bundle)
    resolved_evidence = None
    if include_evidence:
        resolved_evidence = EvidenceIndex(
            (
                EvidenceRecord(
                    evidence_id="ev_doc",
                    job_id="job_report",
                    source_type="spec_document",
                    source_path="README.md",
                    content_hash="hash-doc",
                    summary="README evidence",
                ),
                EvidenceRecord(
                    evidence_id="ev_py",
                    job_id="job_report",
                    source_type="file",
                    source_path="pyproject.toml",
                    content_hash="hash-py",
                    summary="Python evidence",
                ),
            )
        )
    return ReleaseNoteContent(
        title="Release Note",
        release_name="v0.1.0",
        repository="example/repo",
        generated_at="2026-06-13T00:00:00+00:00",
        analytics=bundle,
        diagrams=diagrams,
        evidence=resolved_evidence,
    )
