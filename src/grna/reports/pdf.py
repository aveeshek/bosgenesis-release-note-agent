"""PDF rendering for release-note reports."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from grna.reports.markdown import ReleaseNoteContent


@dataclass(frozen=True, slots=True)
class PdfRenderResult:
    """Result of an attempted PDF render."""

    ok: bool
    pdf_bytes: bytes | None
    renderer: str
    html_preserved: bool
    markdown_preserved: bool
    error_message: str | None = None


class PdfReleaseNoteRenderer:
    """Render a styled PDF using ReportLab when available."""

    renderer_name = "reportlab"

    def render(
        self,
        content: ReleaseNoteContent,
        *,
        html: str,
        markdown: str,
    ) -> PdfRenderResult:
        """Render PDF bytes while preserving source artifacts on failure."""

        try:
            pdf_bytes = self._render_with_reportlab(content)
        except Exception as exc:  # pragma: no cover - exact dependency failures vary.
            return PdfRenderResult(
                ok=False,
                pdf_bytes=None,
                renderer=self.renderer_name,
                html_preserved=bool(html),
                markdown_preserved=bool(markdown),
                error_message=str(exc),
            )
        return PdfRenderResult(
            ok=True,
            pdf_bytes=pdf_bytes,
            renderer=self.renderer_name,
            html_preserved=bool(html),
            markdown_preserved=bool(markdown),
        )

    def _render_with_reportlab(self, content: ReleaseNoteContent) -> bytes:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            PageBreak,
            Paragraph,
            Preformatted,
            SimpleDocTemplate,
            Spacer,
        )

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=16 * mm,
            bottomMargin=18 * mm,
            title=content.title,
            author="BOS Genesis Release Note Agent",
        )
        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="BrandEyebrow",
                parent=styles["Normal"],
                textColor=colors.HexColor("#E20074"),
                fontSize=8,
                leading=10,
                spaceAfter=5,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Muted",
                parent=styles["Normal"],
                textColor=colors.HexColor("#52606D"),
                fontSize=8,
                leading=10,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Callout",
                parent=styles["Normal"],
                backColor=colors.HexColor("#F5F7FA"),
                borderColor=colors.HexColor("#D9E2EC"),
                borderWidth=0.5,
                borderPadding=7,
                fontSize=9,
                leading=12,
                spaceBefore=8,
                spaceAfter=8,
            )
        )
        story: list[Any] = [
            Paragraph("BOS Genesis Release Note Agent", styles["BrandEyebrow"]),
            Paragraph(_xml(content.title), styles["Title"]),
            Paragraph("Commercial-grade release notes from repository evidence", styles["Muted"]),
            Spacer(1, 8),
            Paragraph(_project_intent(content), styles["Callout"]),
            _table(
                [
                    ["Release", content.release_name, "Repository", content.repository],
                    ["Generated", content.generated_at, "Job ID", content.analytics.job_id],
                    [
                        "Evidence Sources",
                        len(content.analytics.evidence_ids),
                        "Known Gaps",
                        len(content.analytics.gaps),
                    ],
                ]
            ),
            Spacer(1, 12),
            Paragraph("Headline Metrics", styles["Heading2"]),
            _table(_metric_rows(content)),
            PageBreak(),
        ]

        sections = [
            ("Executive Summary", _project_intent(content), content.analytics.gaps),
            ("Technology Inventory", _technology_text(content), ()),
            (
                "Architecture And Diagrams",
                "Mermaid diagram source is preserved below.",
                content.diagrams.gaps,
            ),
            ("Test And Coverage Analytics", _test_text(content), ()),
            (
                "Risk And Human Review",
                "Human release ownership remains required.",
                content.analytics.warnings,
            ),
            ("Evidence Appendix", "Evidence records used by report sections.", ()),
        ]
        for title, body, gaps in sections:
            story.append(Paragraph(_xml(title), styles["Heading1"]))
            story.append(Paragraph(_xml(body), styles["Normal"]))
            for gap in gaps:
                story.append(Paragraph(f"Missing evidence: {_xml(gap)}", styles["Muted"]))
            if title == "Architecture And Diagrams":
                for diagram in content.diagrams.diagrams:
                    story.append(Paragraph(_xml(diagram.title), styles["Heading2"]))
                    story.append(Paragraph(_xml(diagram.caption), styles["Muted"]))
                    story.append(Preformatted(diagram.source, styles["Code"]))
            if title == "Evidence Appendix":
                story.append(_table(_evidence_rows(content)))
            story.append(Spacer(1, 10))

        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        return buffer.getvalue()


def _footer(canvas: Any, doc: Any) -> None:
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#52606D"))
    canvas.drawString(14 * mm, 10 * mm, "Generated by BOS Genesis Release Note Agent")
    canvas.drawRightString(196 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _table(rows: list[list[Any]]) -> Any:
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    table = Table([[_xml(cell) for cell in row] for row in rows], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9E2EC")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5F7FA")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F2933")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _metric_rows(content: ReleaseNoteContent) -> list[list[Any]]:
    commits = content.analytics.sections.get("commits")
    tests = content.analytics.sections.get("test_coverage")
    commit_count = commits.data.get("commit_count", 0) if commits else 0
    test_count = len(tests.data.get("test_sources", [])) if tests else 0
    return [
        ["Metric", "Value", "Evidence"],
        ["Commits", commit_count, "Commit analyzer"],
        ["Test files", test_count, "Test analyzer"],
        ["Evidence IDs", len(content.analytics.evidence_ids), "Evidence index"],
        ["Known gaps", len(content.analytics.gaps), "Analytics bundle"],
    ]


def _evidence_rows(content: ReleaseNoteContent) -> list[list[Any]]:
    rows: list[list[Any]] = [["Evidence ID", "Source", "Summary"]]
    for evidence_id in content.analytics.evidence_ids:
        record = content.evidence.get(evidence_id) if content.evidence else None
        rows.append(
            [
                evidence_id,
                record.source_path if record else "Not available",
                record.summary if record else "Evidence metadata not available.",
            ]
        )
    return rows


def _project_intent(content: ReleaseNoteContent) -> str:
    section = content.analytics.sections.get("documentation")
    if not section:
        return "Project intent is not available because documentation analysis is missing."
    intent = section.data.get("project_intent", {})
    text = intent.get("text") or "Project intent is unavailable from current evidence."
    source = intent.get("source", "unavailable")
    evidence = intent.get("evidence_id")
    suffix = f" Evidence: {evidence}." if evidence else ""
    return f"{text} Intent source: {source}.{suffix}"


def _technology_text(content: ReleaseNoteContent) -> str:
    section = content.analytics.sections.get("technology")
    if not section:
        return "Technology inventory is not available from repository evidence."
    findings = section.data.get("findings", [])
    if not findings:
        return "No technology findings were detected."
    return ", ".join(str(finding.get("name", "Unknown")) for finding in findings[:12])


def _test_text(content: ReleaseNoteContent) -> str:
    section = content.analytics.sections.get("test_coverage")
    if not section:
        return "Test and coverage evidence is not available from repository files."
    data = section.data
    return (
        f"Test source files: {len(data.get('test_sources', []))}. "
        f"Parsed test reports: {len(data.get('test_reports', []))}. "
        f"Coverage reports: {len(data.get('coverage_reports', []))}."
    )


def _xml(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
