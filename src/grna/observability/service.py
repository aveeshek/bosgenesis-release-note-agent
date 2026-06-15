"""BOS Genesis-style observability service."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from grna.config import AppConfig
from grna.logging_config import get_logger
from grna.observability.models import AuditEvent, PhaseMetric

LOGGER = get_logger(__name__)
_OTEL_CONFIGURED = False
_SECRET_KEYS = ("secret", "token", "password", "credential", "apikey", "api_key", "key")


@dataclass(frozen=True, slots=True)
class ObservabilitySettings:
    """Runtime knobs for optional observability sinks."""

    langfuse_enabled: bool = True
    langfuse_endpoint: str = "http://langfuse-web.bosgenesis.svc.cluster.local:3000"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    signoz_enabled: bool = True
    otlp_endpoint: str = "http://signoz-otel-collector.signoz.svc.cluster.local:4317"
    audit_enabled: bool = True
    phase_metrics_enabled: bool = True
    warning_taxonomy_enabled: bool = True

    @classmethod
    def from_config(cls, config: AppConfig) -> ObservabilitySettings:
        """Map release-note app config into the shared BOS Genesis contract."""

        return cls(
            langfuse_enabled=config.enable_langfuse,
            langfuse_endpoint=config.langfuse_endpoint,
            langfuse_public_key=config.langfuse_public_key,
            langfuse_secret_key=config.langfuse_secret_key,
            signoz_enabled=config.enable_otel,
            otlp_endpoint=config.otlp_endpoint,
            audit_enabled=config.enable_observability_audit,
            phase_metrics_enabled=config.enable_observability_phase_metrics,
            warning_taxonomy_enabled=config.enable_observability_warning_taxonomy,
        )


class ObservabilityService:
    """Create per-job redacted tracing, metrics, and audit collectors."""

    def __init__(self, settings: ObservabilitySettings) -> None:
        self._settings = settings
        self._otel_status = _configure_otel(settings)
        self._langfuse_client, self._langfuse_status = _configure_langfuse(settings)

    def trace_ids(self, job_id: str) -> dict[str, str | None]:
        """Return stable trace identifiers for optional external sinks."""

        return {
            "langfuse": (
                _stable_langfuse_trace_id(job_id, self._langfuse_client)
                if self._settings.langfuse_enabled
                else None
            ),
            "signoz": (
                _stable_trace_id("signoz", job_id) if self._settings.signoz_enabled else None
            ),
        }

    def start_run(
        self,
        *,
        job_id: str,
        correlation_id: str,
        repository: str,
        release_name: str | None,
        runtime: str,
        caller: str,
    ) -> ObservabilityRun:
        """Start a per-job observability collector."""

        return ObservabilityRun(
            settings=self._settings,
            context={
                "job_id": job_id,
                "run_id": job_id,
                "correlation_id": correlation_id,
                "repository": repository,
                "release_name": release_name,
                "runtime": runtime,
                "caller": caller,
                "agent_name": "bosgenesis-release-note-agent",
                "source_namespace": "github",
                "target_namespace": "bosgenesis",
            },
            trace_ids=self.trace_ids(job_id),
            sink_status={
                "structured_audit": "enabled" if self._settings.audit_enabled else "disabled",
                "phase_latency_metrics": (
                    "enabled" if self._settings.phase_metrics_enabled else "disabled"
                ),
                "warning_taxonomy": (
                    "enabled" if self._settings.warning_taxonomy_enabled else "disabled"
                ),
                "signoz": self._otel_status,
                "langfuse": self._langfuse_status,
            },
            langfuse_client=self._langfuse_client,
        )


class ObservabilityRun:
    """Per-job in-memory observability collector."""

    def __init__(
        self,
        *,
        settings: ObservabilitySettings,
        context: dict[str, Any],
        trace_ids: dict[str, str | None],
        sink_status: dict[str, str],
        langfuse_client: Any | None = None,
    ) -> None:
        self._settings = settings
        self.context = context
        self.trace_ids = trace_ids
        self.audit_events: list[AuditEvent] = []
        self.phase_metrics: list[PhaseMetric] = []
        self._warning_taxonomy: dict[str, int] = {}
        self._sink_status = sink_status
        self._langfuse_client = langfuse_client
        self._service_details = redact(
            {
                "langfuse_endpoint": settings.langfuse_endpoint,
                "signoz_otlp_endpoint": settings.otlp_endpoint,
            }
        )

    def phase(self, phase: str, *, action: str | None = None) -> _PhaseScope:
        """Create a phase timing scope."""

        return _PhaseScope(self, phase=phase, action=action or phase)

    def record_event(
        self,
        *,
        event_type: str,
        phase: str,
        action: str,
        status: str,
        severity: str = "info",
        latency_ms: float | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Append and log a redacted audit event."""

        if not self._settings.audit_enabled:
            return
        event = AuditEvent(
            event_type=event_type,
            phase=phase,
            action=action,
            status=status,
            severity=severity,
            latency_ms=latency_ms,
            message=message,
            details=redact(details or {}),
        )
        self.audit_events.append(event)
        LOGGER.info("release_note_audit_event", extra={**self.context, **event.to_dict()})

    def record_artifact_generated(
        self,
        *,
        artifact_type: str,
        relative_path: str,
        size_bytes: int,
        checksum_sha256: str,
    ) -> None:
        """Record artifact-generation audit metadata."""

        self.record_event(
            event_type="artifact_generated",
            phase="rendering_artifacts",
            action="save_artifact",
            status="ok",
            details={
                "artifact_type": artifact_type,
                "relative_path": relative_path,
                "size_bytes": size_bytes,
                "checksum_sha256": checksum_sha256,
            },
        )

    def record_warning(self, warning: str, *, phase: str = "warning_taxonomy") -> None:
        """Classify and audit a warning or known gap."""

        if not self._settings.warning_taxonomy_enabled:
            return
        category = classify_warning(warning)
        self._warning_taxonomy[category] = self._warning_taxonomy.get(category, 0) + 1
        self.record_event(
            event_type="warning_classified",
            phase=phase,
            action="classify_warning",
            status="warning",
            severity="warning",
            message=str(redact(warning))[:240],
            details={"warning_category": category},
        )

    def record_warnings(
        self,
        warnings: list[str] | tuple[str, ...],
        *,
        phase: str = "warning_taxonomy",
    ) -> None:
        """Classify several warnings."""

        for warning in warnings:
            self.record_warning(warning, phase=phase)

    def record_release_reasoning(self, analytics_summary: dict[str, Any]) -> None:
        """Emit redacted release-note reasoning metadata to audit and Langfuse."""

        details = {
            "analytics_summary": redact(analytics_summary),
            "prompt_payload_policy": "redacted_metadata_only_no_prompt_or_response_text",
        }
        self.record_event(
            event_type="langfuse_reasoning_trace",
            phase="release_reasoning",
            action="record_release_note_metadata",
            status=(
                "emitted"
                if self._sink_status.get("langfuse") == "enabled"
                else self._sink_status.get("langfuse", "disabled")
            ),
            details=details,
        )
        self._emit_langfuse_release_reasoning(details)

    def summary(self) -> dict[str, Any]:
        """Return the manifest-compatible observability payload."""

        return {
            "schema_version": "phase13.observability.v1",
            "trace_ids": self.trace_ids,
            "sinks": self._sink_status,
            "service_details": self._service_details,
            "context": redact(self.context),
            "phase_metrics": [metric.to_dict() for metric in self.phase_metrics],
            "phase_latency_ms": {
                metric.phase: round(metric.latency_ms, 3) for metric in self.phase_metrics
            },
            "warning_taxonomy": dict(sorted(self._warning_taxonomy.items())),
            "audit_events": [event.to_dict() for event in self.audit_events],
            "audit_event_count": len(self.audit_events),
            "redaction_status": "metadata_only_no_secret_payload",
        }

    def _record_phase_complete(self, phase: str, status: str, latency_ms: float) -> None:
        if self._settings.phase_metrics_enabled:
            self.phase_metrics.append(
                PhaseMetric(phase=phase, status=status, latency_ms=latency_ms)
            )
        self.record_event(
            event_type="phase_completed",
            phase=phase,
            action=phase,
            status=status,
            severity="error" if status == "failed" else "info",
            latency_ms=latency_ms,
        )

    def _emit_langfuse_release_reasoning(self, details: dict[str, Any]) -> None:
        if self._sink_status.get("langfuse") != "enabled" or self._langfuse_client is None:
            return
        try:
            metadata = redact({**self.context, **details})
            if hasattr(self._langfuse_client, "trace"):
                session_id = str(
                    self.context.get("correlation_id") or self.context.get("job_id")
                )
                trace = self._langfuse_client.trace(
                    id=self.trace_ids.get("langfuse"),
                    name="bosgenesis_release_note_reasoning",
                    user_id=str(self.context.get("caller") or "unknown"),
                    session_id=session_id,
                    metadata=metadata,
                    tags=["bosgenesis", "release-note-agent", "phase13"],
                )
                if hasattr(trace, "event"):
                    trace.event(
                        name="release_note_metadata",
                        metadata=redact(details),
                        level="DEFAULT",
                    )
            elif hasattr(self._langfuse_client, "create_event"):
                self._langfuse_client.create_event(
                    trace_context={"trace_id": self.trace_ids.get("langfuse")},
                    name="release_note_metadata",
                    input={"policy": "redacted_metadata_only_no_prompt_or_response_text"},
                    output={"status": "metadata_recorded"},
                    metadata=metadata,
                    level="DEFAULT",
                )
            else:
                raise AttributeError("Langfuse client has no supported trace/event API")
            if hasattr(self._langfuse_client, "flush"):
                self._langfuse_client.flush()
        except Exception as exc:  # pragma: no cover - telemetry must not break scans.
            self._sink_status["langfuse"] = "enabled_export_failed"
            self.record_event(
                event_type="telemetry_export_failed",
                phase="release_reasoning",
                action="emit_langfuse_release_note_metadata",
                status="failed",
                severity="warning",
                message=str(exc),
            )


class _PhaseScope(AbstractContextManager["_PhaseScope"]):
    def __init__(self, run: ObservabilityRun, *, phase: str, action: str) -> None:
        self._run = run
        self._phase = phase
        self._action = action
        self._started = 0.0
        self._span = None

    def __enter__(self) -> _PhaseScope:
        self._started = perf_counter()
        self._run.record_event(
            event_type="phase_started",
            phase=self._phase,
            action=self._action,
            status="started",
        )
        self._span = _start_otel_span(self._phase, self._run.context)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        latency_ms = (perf_counter() - self._started) * 1000
        status = "failed" if exc is not None else "ok"
        if self._span is not None:
            try:
                if exc is not None and hasattr(self._span, "record_exception"):
                    self._span.record_exception(exc)
                self._span.__exit__(exc_type, exc, traceback)
            except Exception:  # pragma: no cover - telemetry must not break scans.
                LOGGER.warning("otel_span_close_failed", extra=self._run.context)
        self._run._record_phase_complete(self._phase, status, latency_ms)
        return False


def record_artifact_download_audit(
    *,
    job_id: str,
    artifact_id: str,
    artifact_type: str,
    relative_path: str,
    status: str,
) -> None:
    """Emit a structured artifact download audit log."""

    event = AuditEvent(
        event_type="artifact_download",
        phase="artifact_download",
        action="download_artifact",
        status=status,
        details={
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "relative_path": relative_path,
        },
    )
    LOGGER.info("release_note_audit_event", extra={"job_id": job_id, **event.to_dict()})


def classify_warning(warning: str) -> str:
    """Classify known gaps and warnings using the shared BOS Genesis taxonomy style."""

    lowered = warning.lower()
    if "coverage" in lowered or "test" in lowered or "junit" in lowered or "pytest" in lowered:
        return "validation"
    if "hld" in lowered or "lld" in lowered or "adr" in lowered or "spec" in lowered:
        return "documentation"
    if "deploy" in lowered or "helm" in lowered or "kubernetes" in lowered or "docker" in lowered:
        return "deployment"
    if "secret" in lowered or "credential" in lowered or "redact" in lowered:
        return "safety"
    if "unsupported" in lowered or "partial" in lowered:
        return "analysis"
    if "git" in lowered or "commit" in lowered or "repository" in lowered:
        return "repository"
    return "general"


def redact(value: Any) -> Any:
    """Redact likely secret values while preserving useful metadata."""

    if isinstance(value, dict):
        return {
            key: "***REDACTED***" if _is_secret_key(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, str) and _looks_secret_like(value):
        return "***REDACTED***"
    return value


def _configure_otel(settings: ObservabilitySettings) -> str:
    global _OTEL_CONFIGURED
    if not settings.signoz_enabled:
        return "disabled"
    if not settings.otlp_endpoint:
        return "enabled_endpoint_missing"
    if _OTEL_CONFIGURED:
        return "enabled"
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return "enabled_sdk_unavailable"
    try:
        provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": "bosgenesis-release-note-agent",
                    "service.namespace": "bosgenesis",
                    "deployment.environment": "bosgenesis-lab",
                }
            )
        )
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=settings.otlp_endpoint,
                    insecure=settings.otlp_endpoint.startswith("http://"),
                )
            )
        )
        trace.set_tracer_provider(provider)
        _OTEL_CONFIGURED = True
    except Exception as exc:  # pragma: no cover - telemetry must not break scans.
        LOGGER.warning("otel_config_failed", extra={"error": str(exc)})
        return "enabled_config_failed"
    return "enabled"


def _configure_langfuse(settings: ObservabilitySettings) -> tuple[Any | None, str]:
    if not settings.langfuse_enabled:
        return None, "disabled"
    if not settings.langfuse_endpoint:
        return None, "enabled_endpoint_missing"
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None, "enabled_credentials_missing"
    try:
        from langfuse import Langfuse
    except ImportError:
        return None, "enabled_sdk_unavailable"
    try:
        return (
            Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_endpoint,
            ),
            "enabled",
        )
    except Exception as exc:  # pragma: no cover - telemetry must not break scans.
        LOGGER.warning("langfuse_config_failed", extra={"error": str(exc)})
        return None, "enabled_config_failed"


def _start_otel_span(phase: str, context: dict[str, Any]) -> Any | None:
    try:
        from opentelemetry import trace
    except ImportError:
        return None
    tracer = trace.get_tracer("bosgenesis.release_note_agent")
    span = tracer.start_as_current_span(f"release_note.{phase}")
    manager = span.__enter__()
    for key, value in context.items():
        if value is not None and hasattr(manager, "set_attribute"):
            manager.set_attribute(f"release_note.{key}", str(value))
    return span


def _stable_trace_id(prefix: str, job_id: str) -> str:
    return f"{prefix}-{uuid5(NAMESPACE_URL, f'bosgenesis-release-note:{prefix}:{job_id}').hex}"


def _stable_langfuse_trace_id(job_id: str, client: Any | None) -> str:
    if client is not None and hasattr(client, "create_trace_id"):
        return str(client.create_trace_id(seed=job_id))
    try:
        from langfuse import Langfuse

        if hasattr(Langfuse, "create_trace_id"):
            return str(Langfuse.create_trace_id(seed=job_id))
    except ImportError:
        pass
    return uuid5(NAMESPACE_URL, f"bosgenesis-release-note:langfuse:{job_id}").hex


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in _SECRET_KEYS)


def _looks_secret_like(value: str) -> bool:
    lowered = value.lower()
    if any(marker in lowered for marker in ("authorization:", "bearer ", "x-api-key")):
        return True
    return False
