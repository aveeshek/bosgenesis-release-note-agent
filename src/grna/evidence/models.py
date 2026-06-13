"""Evidence data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

EvidenceSourceType = Literal[
    "file",
    "commit",
    "fact",
    "test_report",
    "coverage_report",
    "spec_document",
    "generated",
    "inference",
]


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Traceable evidence item used by analyzers and reports."""

    evidence_id: str
    job_id: str
    source_type: EvidenceSourceType
    source_path: str | None
    content_hash: str
    summary: str
    sensitive: bool = False
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceIndex:
    """Lookup structure for evidence records."""

    records: tuple[EvidenceRecord, ...]

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        """Return an evidence item by ID."""

        for record in self.records:
            if record.evidence_id == evidence_id:
                return record
        return None

    def require(self, evidence_id: str) -> EvidenceRecord:
        """Return an evidence item or raise `KeyError`."""

        record = self.get(evidence_id)
        if record is None:
            raise KeyError(evidence_id)
        return record

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return {"records": [record.to_dict() for record in self.records]}
