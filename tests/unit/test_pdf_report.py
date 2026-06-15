from grna.diagrams import MermaidDiagramGenerator
from grna.evidence import AnalyticsBundle, AnalyticsSection, EvidenceIndex, EvidenceRecord
from grna.reports import (
    HtmlReleaseNoteRenderer,
    MarkdownReleaseNoteRenderer,
    PdfReleaseNoteRenderer,
    ReleaseNoteContent,
)


def test_pdf_renderer_generates_pdf_or_structured_dependency_failure() -> None:
    content = _content()
    html = HtmlReleaseNoteRenderer().render(content)
    markdown = MarkdownReleaseNoteRenderer().render(content)

    result = PdfReleaseNoteRenderer().render(content, html=html, markdown=markdown)

    assert result.renderer == "html-browser"
    assert result.html_preserved is True
    assert result.markdown_preserved is True
    if result.ok:
        assert result.pdf_bytes is not None
        assert result.pdf_bytes.startswith(b"%PDF")
        assert len(result.pdf_bytes) > 1000
    else:
        assert result.pdf_bytes is None
        assert result.error_message


def test_pdf_renderer_preserves_html_and_markdown_on_render_failure(monkeypatch) -> None:
    content = _content()
    renderer = PdfReleaseNoteRenderer()

    def fail_html(_: str) -> bytes:
        raise RuntimeError("html backend unavailable")

    monkeypatch.setattr(renderer, "_render_html_with_browser", fail_html)

    result = renderer.render(content, html="<html></html>", markdown="# report")

    assert result.ok is False
    assert result.pdf_bytes is None
    assert result.html_preserved is True
    assert result.markdown_preserved is True
    assert "html backend unavailable" in result.error_message


def test_pdf_renderer_prefers_html_backend(monkeypatch) -> None:
    content = _content()
    renderer = PdfReleaseNoteRenderer()

    monkeypatch.setattr(renderer, "_render_html_with_browser", lambda _: b"%PDF-styled")

    result = renderer.render(content, html="<html></html>", markdown="# report")

    assert result.ok is True
    assert result.renderer == "html-browser"
    assert result.pdf_bytes == b"%PDF-styled"


def test_pdf_renderer_reportlab_fallback_is_opt_in(monkeypatch) -> None:
    content = _content()
    renderer = PdfReleaseNoteRenderer()

    monkeypatch.setattr(
        renderer,
        "_render_html_with_browser",
        lambda _: (_ for _ in ()).throw(RuntimeError("html backend unavailable")),
    )
    monkeypatch.setattr(renderer, "_render_with_reportlab", lambda _: b"%PDF-fallback")

    default_result = renderer.render(content, html="<html></html>", markdown="# report")
    fallback_result = renderer.render(
        content,
        html="<html></html>",
        markdown="# report",
        allow_reportlab_fallback=True,
    )

    assert default_result.ok is False
    assert default_result.renderer == "html-browser"
    assert fallback_result.ok is True
    assert fallback_result.renderer == "reportlab"
    assert fallback_result.pdf_bytes == b"%PDF-fallback"


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
