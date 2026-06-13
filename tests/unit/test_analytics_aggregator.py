from grna.analyzers.test_coverage import (
    TestCoverageAnalysis as CoverageAnalysisModel,
)
from grna.analyzers.test_coverage import (
    TestSourceFile as CoverageSourceFileModel,
)
from grna.evidence import AnalyticsAggregator, EvidenceIndex, EvidenceRecord


def test_analytics_aggregator_combines_outputs_and_evidence_ids() -> None:
    evidence = EvidenceRecord(
        evidence_id="ev_test",
        job_id="job_analytics",
        source_type="file",
        source_path="tests/test_app.py",
        content_hash="hash",
        summary="test file",
    )
    test_output = CoverageAnalysisModel(
        test_sources=(CoverageSourceFileModel("tests/test_app.py", 42, "ev_test"),),
        test_reports=(),
        coverage_reports=(),
        gaps=("No coverage report evidence detected.",),
    )

    bundle = AnalyticsAggregator(
        job_id="job_analytics",
        evidence_index=EvidenceIndex((evidence,)),
    ).aggregate(test_coverage=test_output)

    payload = bundle.to_dict()
    assert payload["job_id"] == "job_analytics"
    test_sources = payload["sections"]["test_coverage"]["data"]["test_sources"]
    assert test_sources[0]["path"] == "tests/test_app.py"
    assert payload["sections"]["test_coverage"]["evidence_ids"] == ["ev_test"]
    assert payload["gaps"] == ["No coverage report evidence detected."]
    assert payload["evidence_ids"] == ["ev_test"]


def test_analytics_aggregator_normalizes_missing_outputs_and_warnings() -> None:
    bundle = AnalyticsAggregator("job_analytics").aggregate(
        technology={"warnings": ["low confidence"], "gaps": ["missing manifest"]},
        commits=None,
    )
    payload = bundle.to_dict()

    assert payload["sections"]["commits"]["data"] == {}
    assert payload["sections"]["commits"]["gaps"] == ["commits analyzer output is unavailable."]
    assert payload["gaps"] == [
        "commits analyzer output is unavailable.",
        "missing manifest",
    ]
    assert payload["warnings"] == ["low confidence"]


def test_analytics_aggregator_rejects_non_serializable_output() -> None:
    class NotSerializable:
        pass

    try:
        AnalyticsAggregator("job_analytics").aggregate(bad=NotSerializable())
    except TypeError as exc:
        assert "analyzer output is not JSON serializable" in str(exc)
    else:
        raise AssertionError("expected TypeError")
