# Report Templates Specification

## Intent

Store template assets used by the report generation module.

## Role

- Define Markdown and HTML layout templates.
- Keep release-note structure consistent across runs.
- Support reusable sections such as executive summary, evidence tables, diagrams, and analytics tables.

## Inputs

- Template context containing release metadata, analytics, evidence, diagrams, gaps, and artifact links.
- Optional branding or output profile settings.

## Outputs

- Rendered Markdown sections.
- Rendered HTML pages.
- Intermediate content used by PDF rendering.

## Expected Templates

- Release note Markdown template implemented in code by `MarkdownReleaseNoteRenderer` until external templates are introduced.
- Release note HTML template implemented in code by `HtmlReleaseNoteRenderer` until external Jinja templates are introduced.
- Executive summary template.
- Evidence appendix template.
- Diagram section template.
- Analytics table template.

## Design Rules

- Templates must not contain business logic beyond simple presentation conditionals.
- Template variables must be explicit and documented.
- Unknown or missing values must render as clear `Not available` messages.
- HTML templates must be suitable for PDF conversion.
- Keep generated reports professional, compact, and readable.
- HTML templates must remain self-contained with inline CSS and no external network assets.
- PDF rendering must preserve source HTML and Markdown artifacts if the PDF backend fails.
