# Observability Module Specification

## Intent

Make scan jobs, analyzer behavior, artifact generation, and failures visible through structured logs, metrics, traces, and audit events.

## Role

- Provide structured logging helpers.
- Emit job-stage lifecycle events.
- Expose metrics for job count, failures, durations, repository size, analyzer duration, and artifact generation duration.
- Provide optional OpenTelemetry and Langfuse integration points.
- Record audit events for job and artifact operations.

## Inputs

- Job lifecycle events.
- Analyzer start, completion, warning, and failure events.
- Artifact generation events.
- Runtime configuration for telemetry backends.

## Outputs

- Structured log records.
- Metrics.
- Trace spans.
- Audit records.
- `observability.json` artifact with `phase13.observability.v1` schema.

## Design Rules

- Observability must not expose secrets or raw credential values.
- Every long-running stage should have start, completion, duration, and failure signals.
- Observability helpers must be lightweight and safe to call from all modules.
- Optional telemetry backends must fail closed without breaking scans.
- Logs should include `job_id`, `stage`, `event`, `duration_ms`, and `status` where applicable.

## Implemented Contract

- `ObservabilitySettings` mirrors the BOS Genesis MoP creation agent settings for
  Langfuse, SigNoz/OpenTelemetry, audit events, phase metrics, and warning
  taxonomy.
- Default service endpoints match the shared namespace:
  `http://langfuse-web.bosgenesis.svc.cluster.local:3000` and
  `http://signoz-otel-collector.signoz.svc.cluster.local:4317`.
- `ObservabilityService.start_run` creates stable Langfuse and SigNoz trace IDs
  per `job_id`; disabled sinks produce `null` trace IDs and explicit sink status.
- `ObservabilityRun.phase` emits `phase_started` and `phase_completed` audit
  events, records latency metrics, and opens optional OpenTelemetry spans when
  SDKs are installed.
- Artifact saves emit `artifact_generated` audit events with artifact type,
  relative path, size, and checksum.
- REST artifact downloads emit `artifact_download` audit logs.
- Known gaps and warnings are classified into a warning taxonomy compatible with
  the MoP agent pattern.
- Logs and artifact observability payloads include `job_id`, `stage`, `event`,
  and `status`, and use `metadata_only_no_secret_payload` redaction.
