"""Structured observability records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class AuditEvent:
    """Redacted audit event compatible with BOS Genesis observability manifests."""

    event_type: str
    phase: str
    action: str
    status: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    latency_ms: float | None = None
    severity: str = "info"
    warning_category: str | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event for logs and artifact metadata."""

        payload: dict[str, Any] = {
            "timestamp": self.timestamp,
            "event": self.event_type,
            "event_type": self.event_type,
            "stage": self.phase,
            "phase": self.phase,
            "action": self.action,
            "status": self.status,
            "severity": self.severity,
            "redaction_status": "metadata_only_no_secret_payload",
        }
        if self.latency_ms is not None:
            payload["latency_ms"] = round(self.latency_ms, 3)
        if self.warning_category:
            payload["warning_category"] = self.warning_category
        if self.message:
            payload["event_message"] = self.message
        if self.details:
            payload["details"] = self.details
        return payload


@dataclass(slots=True)
class PhaseMetric:
    """Duration metric for a scan phase."""

    phase: str
    status: str
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize the metric for observability manifests."""

        return {
            "phase": self.phase,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 3),
        }
