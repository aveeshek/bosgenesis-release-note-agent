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

