from grna.analyzers import InventoryFile, RepositoryInventory
from grna.evidence import EvidenceIndexer, make_evidence_id, redact_sensitive_text


def test_evidence_ids_are_deterministic() -> None:
    first = make_evidence_id("job_001", "file", "README.md", "abc123")
    second = make_evidence_id("job_001", "file", "readme.md", "abc123")

    assert first == second
    assert first.startswith("ev_")


def test_evidence_indexer_generates_records_and_links_inventory() -> None:
    inventory = RepositoryInventory(
        root_path="/repo",
        files=(
            InventoryFile(
                path="README.md",
                category="docs",
                size_bytes=10,
                checksum_sha256="hash-readme",
                important=True,
            ),
            InventoryFile(
                path="coverage/coverage.xml",
                category="coverage",
                size_bytes=20,
                checksum_sha256="hash-coverage",
                important=True,
            ),
        ),
        total_files=2,
        total_size_bytes=30,
        category_counts={"docs": 1, "coverage": 1},
        skipped_directories=(),
        important_files=("README.md", "coverage/coverage.xml"),
    )

    linked_inventory, index = EvidenceIndexer("job_001").index_inventory(inventory)

    assert all(item.evidence_id for item in linked_inventory.files)
    readme_evidence = index.require(linked_inventory.find_file("README.md").evidence_id)
    coverage_evidence = index.require(
        linked_inventory.find_file("coverage/coverage.xml").evidence_id
    )

    assert readme_evidence.source_type == "spec_document"
    assert readme_evidence.source_path == "README.md"
    assert readme_evidence.metadata["important"] is True
    assert coverage_evidence.source_type == "coverage_report"


def test_evidence_indexer_redacts_sensitive_values() -> None:
    indexer = EvidenceIndexer("job_001")

    record = indexer.fact_record(
        fact_key="config.secret",
        summary="token=abc123 password:supersecret api_key = xyz",
    )

    assert record.sensitive is True
    assert "abc123" not in record.summary
    assert "supersecret" not in record.summary
    assert "xyz" not in record.summary
    assert "[REDACTED]" in record.summary


def test_evidence_index_lookup_by_id() -> None:
    indexer = EvidenceIndexer("job_001")
    record = indexer.commit_record(
        commit_sha="0123456789abcdef",
        summary="Initial implementation",
        metadata={"author": "Test User"},
    )
    index = indexer.index_records([record])

    assert index.get(record.evidence_id) == record
    assert index.get("missing") is None
    assert index.require(record.evidence_id).metadata["author"] == "Test User"


def test_redaction_helper_is_report_ready() -> None:
    redacted = redact_sensitive_text("Authorization: Bearer abc.def.ghi")

    assert "abc.def.ghi" not in redacted
    assert "[REDACTED]" in redacted
