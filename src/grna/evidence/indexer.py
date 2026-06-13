"""Evidence indexing helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from grna.analyzers.inventory import InventoryFile, RepositoryInventory
from grna.evidence.models import EvidenceIndex, EvidenceRecord, EvidenceSourceType
from grna.utils.hashing import sha256_bytes

SECRET_PATTERNS = (
    re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)(secret|token|api[_-]?key|access[_-]?key)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)(authorization:\s*bearer)\s+([A-Za-z0-9._~+/=-]+)"),
)


class EvidenceIndexer:
    """Build deterministic, report-ready evidence records."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id

    def index_inventory(
        self,
        inventory: RepositoryInventory,
    ) -> tuple[RepositoryInventory, EvidenceIndex]:
        """Create file evidence for all inventory files and link IDs back to the inventory."""

        records: list[EvidenceRecord] = []
        linked_files: list[InventoryFile] = []
        for file in inventory.files:
            record = self.file_record(file)
            records.append(record)
            linked_files.append(file.with_evidence(record.evidence_id))

        linked_inventory = RepositoryInventory(
            root_path=inventory.root_path,
            files=tuple(linked_files),
            total_files=inventory.total_files,
            total_size_bytes=inventory.total_size_bytes,
            category_counts=inventory.category_counts,
            skipped_directories=inventory.skipped_directories,
            important_files=inventory.important_files,
        )
        return linked_inventory, EvidenceIndex(
            tuple(sorted(records, key=lambda item: item.evidence_id))
        )

    def file_record(self, file: InventoryFile) -> EvidenceRecord:
        """Create deterministic evidence for one inventory file."""

        source_type = _source_type_for_file(file)
        summary = redact_sensitive_text(
            f"{file.category} file {file.path} ({file.size_bytes} bytes)"
        )
        return EvidenceRecord(
            evidence_id=make_evidence_id(
                self.job_id,
                source_type,
                file.path,
                file.checksum_sha256,
            ),
            job_id=self.job_id,
            source_type=source_type,
            source_path=file.path,
            content_hash=file.checksum_sha256,
            summary=summary,
            metadata={
                "category": file.category,
                "important": file.important,
                "size_bytes": file.size_bytes,
            },
        )

    def commit_record(
        self,
        commit_sha: str,
        summary: str,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceRecord:
        """Create deterministic evidence for a Git commit fact."""

        clean_summary, sensitive = redact_sensitive_text_with_flag(summary)
        content_hash = sha256_bytes(commit_sha.encode("utf-8"))
        return EvidenceRecord(
            evidence_id=make_evidence_id(self.job_id, "commit", commit_sha, content_hash),
            job_id=self.job_id,
            source_type="commit",
            source_path=commit_sha,
            content_hash=content_hash,
            summary=clean_summary,
            sensitive=sensitive,
            metadata=metadata,
        )

    def fact_record(
        self,
        fact_key: str,
        summary: str,
        source_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceRecord:
        """Create deterministic evidence for an analyzer fact."""

        clean_summary, sensitive = redact_sensitive_text_with_flag(summary)
        content_hash = sha256_bytes(f"{fact_key}|{clean_summary}".encode())
        return EvidenceRecord(
            evidence_id=make_evidence_id(self.job_id, "fact", fact_key, content_hash),
            job_id=self.job_id,
            source_type="fact",
            source_path=source_path,
            content_hash=content_hash,
            summary=clean_summary,
            sensitive=sensitive,
            metadata=metadata,
        )

    def index_records(self, records: Iterable[EvidenceRecord]) -> EvidenceIndex:
        """Return a deterministic lookup index for records."""

        return EvidenceIndex(tuple(sorted(records, key=lambda item: item.evidence_id)))


def make_evidence_id(
    job_id: str,
    source_type: EvidenceSourceType,
    source_key: str | Path | None,
    content_hash: str,
) -> str:
    """Return a stable evidence ID for a job/source/hash tuple."""

    normalized_key = "" if source_key is None else str(source_key).replace("\\", "/").lower()
    seed = f"{job_id}|{source_type}|{normalized_key}|{content_hash}"
    return f"ev_{sha256_bytes(seed.encode('utf-8'))[:20]}"


def redact_sensitive_text(text: str) -> str:
    """Redact common inline secret patterns before text reaches reports."""

    redacted, _ = redact_sensitive_text_with_flag(text)
    return redacted


def redact_sensitive_text_with_flag(text: str) -> tuple[str, bool]:
    """Return redacted text and whether any sensitive value was found."""

    sensitive = False
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted, count = pattern.subn(r"\1=[REDACTED]", redacted)
        sensitive = sensitive or count > 0
    return redacted, sensitive


def _source_type_for_file(file: InventoryFile) -> EvidenceSourceType:
    if file.category == "coverage":
        return "coverage_report"
    if file.category == "test":
        return "test_report"
    if file.category == "docs" and file.important:
        return "spec_document"
    return "file"
