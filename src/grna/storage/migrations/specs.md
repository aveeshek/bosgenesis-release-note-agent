# Storage Migrations Specification

## Intent

Own database schema evolution for job state, evidence, analytics, artifact metadata, and audit data.

## Role

- Store migration files once schema tooling is selected.
- Define forward-only schema changes for production deployments.
- Support local development database setup.

## Inputs

- Data model requirements from `storage/specs.md`.
- PostgreSQL target schema.
- Migration tool configuration.

## Outputs

- Versioned migration scripts.
- Schema objects for jobs, stages, evidence, analytics, artifacts, and audit events.

## Design Rules

- Migrations must be deterministic and reviewable.
- Avoid destructive migrations unless explicitly planned.
- JSONB fields may store analyzer-specific payloads, but common lookup fields should remain indexed columns.
- Migration naming must include sequence and intent.
- Tests should validate fresh database creation when database-backed tests are added.

