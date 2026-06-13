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

## Implemented Evidence Indexer Contract

- `EvidenceRecord` stores evidence ID, job ID, source type, source path, content hash, report-ready summary, sensitivity flag, and metadata.
- `EvidenceIndex` provides lookup by ID through `get()` and strict lookup through `require()`.
- `EvidenceIndexer` creates deterministic evidence IDs from job ID, source type, normalized source key, and content hash.
- Inventory evidence links back to `InventoryFile.evidence_id` without mutating the original inventory object.
- File evidence maps coverage files to `coverage_report`, tests to `test_report`, important docs to `spec_document`, and all other files to `file`.
- Commit evidence is supported from commit SHA and summary metadata.
- Fact evidence is supported for analyzer findings that are not tied one-to-one to a file.
- Redaction hooks remove common password, token, API key, access key, secret, and bearer-token values before evidence can be emitted to reports.
