"""Analytics bundle aggregation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from grna.evidence.models import EvidenceIndex
from grna.storage.models import utc_now_iso


@dataclass(frozen=True, slots=True)
class AnalyticsSection:
    """One analyzer output normalized for report generation."""

    name: str
    data: dict[str, Any]
    gaps: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        payload = asdict(self)
        payload["gaps"] = list(self.gaps)
        payload["warnings"] = list(self.warnings)
        payload["evidence_ids"] = list(self.evidence_ids)
        return payload


@dataclass(frozen=True, slots=True)
class AnalyticsBundle:
    """Single analytics object that can drive report generation."""

    job_id: str
    generated_at: str
    sections: dict[str, AnalyticsSection]
    gaps: tuple[str, ...]
    warnings: tuple[str, ...]
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return {
            "job_id": self.job_id,
            "generated_at": self.generated_at,
            "sections": {
                name: section.to_dict()
                for name, section in sorted(self.sections.items())
            },
            "gaps": list(self.gaps),
            "warnings": list(self.warnings),
            "evidence_ids": list(self.evidence_ids),
        }


class AnalyticsAggregator:
    """Combine analyzer outputs into one report-ready analytics bundle."""

    def __init__(self, job_id: str, evidence_index: EvidenceIndex | None = None) -> None:
        self.job_id = job_id
        self.evidence_index = evidence_index

    def aggregate(self, **outputs: Any) -> AnalyticsBundle:
        """Normalize analyzer outputs into sections with gaps and evidence references."""

        sections: dict[str, AnalyticsSection] = {}
        for name, output in sorted(outputs.items()):
            if output is None:
                sections[name] = AnalyticsSection(
                    name=name,
                    data={},
                    gaps=(f"{name} analyzer output is unavailable.",),
                )
                continue
            data = _to_dict(output)
            sections[name] = AnalyticsSection(
                name=name,
                data=data,
                gaps=tuple(str(item) for item in data.get("gaps", []) if item),
                warnings=tuple(str(item) for item in data.get("warnings", []) if item),
                evidence_ids=tuple(sorted(_collect_evidence_ids(data))),
            )

        all_gaps = _normalize_unique(
            gap
            for section in sections.values()
            for gap in section.gaps
        )
        all_warnings = _normalize_unique(
            warning
            for section in sections.values()
            for warning in section.warnings
        )
        evidence_ids = _normalize_unique(
            evidence_id
            for section in sections.values()
            for evidence_id in section.evidence_ids
        )
        if self.evidence_index is not None:
            evidence_ids = tuple(
                evidence_id for evidence_id in evidence_ids if self.evidence_index.get(evidence_id)
            )
        return AnalyticsBundle(
            job_id=self.job_id,
            generated_at=utc_now_iso(),
            sections=sections,
            gaps=all_gaps,
            warnings=all_warnings,
            evidence_ids=evidence_ids,
        )


def _to_dict(output: Any) -> dict[str, Any]:
    if hasattr(output, "to_dict"):
        return output.to_dict()
    if isinstance(output, dict):
        return output
    raise TypeError(f"analyzer output is not JSON serializable: {type(output)!r}")


def _collect_evidence_ids(value: Any) -> set[str]:
    evidence_ids: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "evidence_id" and isinstance(nested, str):
                evidence_ids.add(nested)
            elif key == "evidence_ids" and isinstance(nested, list | tuple):
                evidence_ids.update(item for item in nested if isinstance(item, str))
            else:
                evidence_ids.update(_collect_evidence_ids(nested))
    elif isinstance(value, list | tuple):
        for item in value:
            evidence_ids.update(_collect_evidence_ids(item))
    return evidence_ids


def _normalize_unique(values) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))
