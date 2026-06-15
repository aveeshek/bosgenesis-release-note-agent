import json
import logging

from grna.observability import (
    ObservabilityService,
    ObservabilitySettings,
    record_artifact_download_audit,
)


def test_observability_summary_records_phase_metrics_audit_and_redaction(caplog) -> None:
    service = ObservabilityService(
        ObservabilitySettings(
            langfuse_enabled=True,
            langfuse_endpoint="http://langfuse-web.bosgenesis.svc.cluster.local:3000",
            langfuse_public_key="public",
            langfuse_secret_key="secret",
            signoz_enabled=False,
        )
    )
    run = service.start_run(
        job_id="scan_obs",
        correlation_id="corr_obs",
        repository="https://github.com/example/project",
        release_name="v1.0.0",
        runtime="pytest",
        caller="pytest",
    )

    with caplog.at_level(logging.INFO):
        with run.phase("fetching_repository", action="fetch_repository"):
            run.record_event(
                event_type="repository_fetched",
                phase="fetching_repository",
                action="fetch_repository",
                status="ok",
                details={"secret_token": "must-not-leak", "file_count": 3},
            )
        run.record_artifact_generated(
            artifact_type="html",
            relative_path="scan_obs/release-note.html",
            size_bytes=123,
            checksum_sha256="abc",
        )
        run.record_warnings(["Missing HLD documentation."])

    summary = run.summary()

    assert summary["schema_version"] == "phase13.observability.v1"
    assert len(summary["trace_ids"]["langfuse"]) == 32
    assert summary["trace_ids"]["signoz"] is None
    assert summary["sinks"]["structured_audit"] == "enabled"
    assert summary["sinks"]["phase_latency_metrics"] == "enabled"
    assert summary["service_details"]["langfuse_endpoint"].startswith("http://langfuse-web")
    assert summary["redaction_status"] == "metadata_only_no_secret_payload"
    assert summary["phase_metrics"][0]["phase"] == "fetching_repository"
    assert summary["phase_metrics"][0]["latency_ms"] >= 0
    assert summary["warning_taxonomy"]["documentation"] == 1
    assert summary["audit_event_count"] == len(summary["audit_events"])
    assert "***REDACTED***" in json.dumps(summary)
    assert "must-not-leak" not in json.dumps(summary)

    records = [record for record in caplog.records if record.message == "release_note_audit_event"]
    assert records
    assert all(hasattr(record, "job_id") for record in records)
    assert all(hasattr(record, "stage") for record in records)
    assert all(hasattr(record, "event") for record in records)
    assert all(hasattr(record, "status") for record in records)


def test_artifact_download_audit_log_shape(caplog) -> None:
    with caplog.at_level(logging.INFO):
        record_artifact_download_audit(
            job_id="scan_download",
            artifact_id="artifact_1",
            artifact_type="pdf",
            relative_path="scan_download/release-note.pdf",
            status="ok",
        )

    record = next(item for item in caplog.records if item.message == "release_note_audit_event")
    assert record.job_id == "scan_download"
    assert record.stage == "artifact_download"
    assert record.event == "artifact_download"
    assert record.status == "ok"
    assert record.details["artifact_type"] == "pdf"
