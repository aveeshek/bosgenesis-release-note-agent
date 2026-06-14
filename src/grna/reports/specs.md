# Reports Module Specification

## Intent

Generate professional release-note artifacts from the normalized evidence and analytics model.

## Role

- Compose release-note content.
- Render Markdown, HTML, and PDF outputs.
- Include diagrams, analytics tables, risk notes, known gaps, and evidence traceability.
- Apply report templates and layout rules.

## Inputs

- Analytics bundle.
- Evidence index.
- Diagram inventory.
- Report options such as release name, formats, branding, and output profile.

## Outputs

- `release-note.md`
- `release-note.html`
- `release-note.pdf`
- Supporting assets and metadata.
- Checksums and artifact records.

## Required Report Sections

- Cover page and release identity.
- Document control.
- Executive summary.
- Release overview.
- Repository overview.
- Project intent.
- Technology inventory.
- Architecture overview.
- C4 and deployment diagrams.
- Feature inventory.
- Interface inventory.
- Code analytics.
- Test analytics.
- Coverage analytics.
- Commit analytics.
- Quality and risk assessment.
- Known gaps.
- Evidence traceability.
- Appendix.

## Design Rules

- Reports must be evidence-backed and human-reviewable.
- Missing tests, coverage, specs, or deployment evidence must be stated clearly.
- Narrative generation must not remove evidence references.
- Markdown output should always be generated for successful scans.
- PDF failure should preserve Markdown and HTML artifacts when possible.

## Implemented Markdown Renderer Contract

- `ReleaseNoteContent` stores title, release name, repository, generated timestamp, analytics bundle, diagram set, and optional evidence index.
- `MarkdownReleaseNoteRenderer` renders the first Markdown report artifact.
- Required sections include document control, executive summary, repository overview, project intent, technology inventory, architecture, interfaces, code, tests, coverage, commits, risks, gaps, evidence traceability, and appendix.
- Mermaid diagrams are embedded as fenced `mermaid` code blocks with captions and confidence values.
- Evidence appendix lists available evidence IDs with source path and summary when an evidence index is provided.
- Missing analytics, coverage, diagram, or evidence data renders as explicit "not available" or missing evidence statements.

## Implemented HTML Renderer Contract

- `ReportThemeTokens` defines configurable BOS Genesis report colors for brand accent, text, borders, surfaces, and readiness/risk states.
- `HtmlReleaseNoteRenderer` renders a complete self-contained HTML document from `ReleaseNoteContent`.
- The HTML artifact includes inline CSS only and must not require external network fonts, scripts, stylesheets, or images.
- The cover page acts as an executive dashboard with release identity, repository, generated timestamp, evidence counts, known gaps, and metric tiles.
- Standard pages include compact headers, numbered sections, tables, callouts, Mermaid source blocks, and evidence blocks.
- HTML is designed as the PDF source with A4 print rules, page-like sections, table wrapping, and explicit missing-evidence language.

## Implemented PDF Renderer Contract

- `PdfReleaseNoteRenderer` is the initial PDF backend and uses ReportLab when the dependency is available.
- `PdfRenderResult` reports whether rendering succeeded, which renderer was used, whether HTML and Markdown artifacts remain preserved, and any error message.
- PDF output preserves the cover/dashboard, page footer with page numbers, compact tables, evidence appendix, and Mermaid source fallback.
- If PDF rendering fails, the renderer returns a structured failure result and does not discard Markdown or HTML source artifacts.
- PDF generation is intentionally report-first and aligned with `docs/report-style-spec.md` through matching theme colors, compact typography, tables, callouts, and evidence traceability.
