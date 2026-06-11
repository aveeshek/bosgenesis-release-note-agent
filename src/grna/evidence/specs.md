# Evidence Module Specification

## Intent

Provide the normalized evidence model that connects repository facts to generated release-note claims.

## Role

- Define evidence item structures.
- Assign stable evidence IDs.
- Store source path, source type, line range, commit SHA, hash, summary, and sensitivity metadata.
- Provide confidence scoring helpers.
- Build traceability links between analytics, diagrams, and release-note sections.

## Inputs

- Repository file metadata.
- Source snippets and parsed facts.
- Commit metadata.
- Test and coverage report data.
- Generated diagram and report references.

## Outputs

- `EvidenceItem` records.
- Confidence scores and labels.
- Evidence lookup/index structures.
- Traceability tables for reports.

## Evidence Types

- `file`
- `commit`
- `test_report`
- `coverage_report`
- `spec_document`
- `generated`
- `inference`

## Design Rules

- Evidence IDs must be deterministic within a job where possible.
- Sensitive values must be redacted before evidence reaches reports.
- Evidence summaries must be concise and factual.
- Claims without evidence must be marked as inferred or unavailable.
- Evidence storage must preserve enough metadata for audit and debugging.

