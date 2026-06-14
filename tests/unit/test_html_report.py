from grna.diagrams import MermaidDiagramGenerator
from grna.evidence import AnalyticsBundle, AnalyticsSection, EvidenceIndex, EvidenceRecord
from grna.reports import HtmlReleaseNoteRenderer, ReleaseNoteContent, ReportThemeTokens


def test_html_report_is_self_contained_and_print_ready() -> None:
    html = HtmlReleaseNoteRenderer().render(_content())

    assert html.startswith("<!doctype html>")
    assert "<style>" in html
    assert "<link" not in html
    assert "<script src" not in html
    assert '<img src="http' not in html
    assert "@page" in html
    assert "page-break-after: always" in html
    assert "--brand-primary: #E20074;" in html


def test_html_report_contains_cover_dashboard_and_report_components() -> None:
    html = HtmlReleaseNoteRenderer().render(_content())

    assert "BOS Genesis Release Note Agent" in html
    assert "Commercial-grade release notes from repository evidence" in html
    assert 'class="metric-grid"' in html
    assert 'class="metric-tile"' in html
    assert "<table>" in html
    assert 'class="callout"' in html
    assert 'class="evidence-block"' in html
    assert "Repository Analysis Flow" in html
    assert 'class="diagram-svg"' in html
    assert "GitHub Repository" in html
    assert "No coverage report evidence detected." in html


def test_html_report_uses_configurable_theme_tokens() -> None:
    html = HtmlReleaseNoteRenderer(
        ReportThemeTokens(brand_primary="#AA0050")
    ).render(_content())

    assert "--brand-primary: #AA0050;" in html


def _content() -> ReleaseNoteContent:
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
                data={
                    "test_sources": [{"path": "tests/test_app.py"}],
                    "coverage_reports": [],
                },
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
    return ReleaseNoteContent(
        title="Release Note",
        release_name="v0.1.0",
        repository="example/repo",
        generated_at="2026-06-13T00:00:00+00:00",
        analytics=bundle,
        diagrams=MermaidDiagramGenerator().generate(bundle),
        evidence=EvidenceIndex(
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
        ),
    )
