from pathlib import Path

from grna.analyzers import RepositoryInventoryAnalyzer, TestCoverageAnalyzer
from grna.evidence import EvidenceIndexer


def test_test_coverage_analyzer_detects_sources_reports_and_coverage(tmp_path) -> None:
    repo = _create_test_coverage_fixture(tmp_path)
    inventory = RepositoryInventoryAnalyzer().analyze(repo)
    linked_inventory, _ = EvidenceIndexer("job_tests").index_inventory(inventory)

    result = TestCoverageAnalyzer().analyze(repo, linked_inventory)

    assert [source.path for source in result.test_sources] == ["tests/test_app.py"]
    assert result.test_sources[0].evidence_id

    junit = next(report for report in result.test_reports if report.path == "reports/junit.xml")
    pytest = next(report for report in result.test_reports if report.path == "reports/pytest.xml")
    assert junit.report_type == "junit"
    assert junit.tests == 3
    assert junit.failures == 1
    assert pytest.report_type == "pytest"
    assert pytest.skipped == 1

    coverage_xml = next(
        report for report in result.coverage_reports if report.path == "coverage.xml"
    )
    lcov = next(report for report in result.coverage_reports if report.path == "coverage/lcov.info")
    jacoco = next(
        report for report in result.coverage_reports if report.path == "coverage/jacoco.xml"
    )
    assert coverage_xml.report_type == "coverage_xml"
    assert coverage_xml.line_rate == 0.75
    assert coverage_xml.packages == ("app",)
    assert lcov.report_type == "lcov"
    assert lcov.lines_valid == 3
    assert lcov.lines_covered == 2
    assert round(lcov.line_rate, 2) == 0.67
    assert jacoco.report_type == "jacoco"
    assert jacoco.lines_valid == 10
    assert jacoco.lines_covered == 8
    assert result.gaps == ()


def test_test_coverage_analyzer_reports_missing_evidence(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# No tests\n", encoding="utf-8")
    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    result = TestCoverageAnalyzer().analyze(repo, inventory)

    assert result.test_sources == ()
    assert result.test_reports == ()
    assert result.coverage_reports == ()
    assert "No test source files detected." in result.gaps
    assert "No pytest or JUnit test report evidence detected." in result.gaps
    assert "No coverage report evidence detected." in result.gaps


def test_test_coverage_analyzer_does_not_invent_coverage_without_reports(tmp_path) -> None:
    repo = tmp_path / "repo"
    test_file = repo / "tests" / "test_app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_app():\n    assert True\n", encoding="utf-8")
    inventory = RepositoryInventoryAnalyzer().analyze(repo)

    result = TestCoverageAnalyzer().analyze(repo, inventory)

    assert len(result.test_sources) == 1
    assert result.coverage_reports == ()
    assert "No coverage report evidence detected." in result.gaps


def _create_test_coverage_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    files = {
        "tests/test_app.py": "def test_app():\n    assert True\n",
        "reports/junit.xml": """
<testsuite tests="3" failures="1" errors="0" skipped="0"></testsuite>
""",
        "reports/pytest.xml": """
<testsuite tests="2" failures="0" errors="0" skipped="1"></testsuite>
""",
        "coverage.xml": """
<coverage line-rate="0.75" lines-covered="30" lines-valid="40">
  <packages>
    <package name="app" />
  </packages>
</coverage>
""",
        "coverage/lcov.info": """
TN:
SF:src/app.py
DA:1,1
DA:2,0
DA:3,1
end_of_record
""",
        "coverage/jacoco.xml": """
<report name="fixture">
  <package name="app">
    <counter type="LINE" missed="2" covered="8" />
  </package>
</report>
""",
    }
    for relative_path, content in files.items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return repo
