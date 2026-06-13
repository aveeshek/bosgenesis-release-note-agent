"""Test and coverage analyzer."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from grna.analyzers.inventory import InventoryFile, RepositoryInventory

TestReportType = Literal["pytest", "junit"]
CoverageReportType = Literal["coverage_xml", "lcov", "jacoco"]


@dataclass(frozen=True, slots=True)
class TestSourceFile:
    """Detected test source file."""

    path: str
    size_bytes: int
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class TestReportSummary:
    """Parsed test report summary."""

    path: str
    report_type: TestReportType
    tests: int
    failures: int
    errors: int
    skipped: int
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class CoverageSummary:
    """Parsed coverage report summary."""

    path: str
    report_type: CoverageReportType
    line_rate: float | None
    lines_covered: int | None
    lines_valid: int | None
    packages: tuple[str, ...] = ()
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class TestCoverageAnalysis:
    """Test and coverage analyzer result."""

    test_sources: tuple[TestSourceFile, ...]
    test_reports: tuple[TestReportSummary, ...]
    coverage_reports: tuple[CoverageSummary, ...]
    gaps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return {
            "test_sources": [source.to_dict() for source in self.test_sources],
            "test_reports": [report.to_dict() for report in self.test_reports],
            "coverage_reports": [report.to_dict() for report in self.coverage_reports],
            "gaps": list(self.gaps),
        }


class TestCoverageAnalyzer:
    """Detect test files and parse common report formats without executing tests."""

    def analyze(
        self,
        repository_path: Path | str,
        inventory: RepositoryInventory,
    ) -> TestCoverageAnalysis:
        """Return test source inventory, parsed reports, and explicit gaps."""

        root = Path(repository_path).resolve()
        test_sources = tuple(
            TestSourceFile(file.path, file.size_bytes, file.evidence_id)
            for file in inventory.files
            if file.category == "test"
        )
        test_reports: list[TestReportSummary] = []
        coverage_reports: list[CoverageSummary] = []

        for file in inventory.files:
            path = root / file.path
            filename = Path(file.path).name.lower()
            if _is_junit_or_pytest_report(file.path):
                parsed = _parse_test_report(path, file)
                if parsed is not None:
                    test_reports.append(parsed)
            if filename == "coverage.xml" or filename == "cobertura.xml":
                parsed_coverage = _parse_coverage_xml(path, file)
                if parsed_coverage is not None:
                    coverage_reports.append(parsed_coverage)
            elif filename == "lcov.info":
                coverage_reports.append(_parse_lcov(path, file))
            elif filename == "jacoco.xml":
                parsed_jacoco = _parse_jacoco(path, file)
                if parsed_jacoco is not None:
                    coverage_reports.append(parsed_jacoco)

        gaps = _gaps(test_sources, test_reports, coverage_reports)
        return TestCoverageAnalysis(
            test_sources=tuple(sorted(test_sources, key=lambda item: item.path)),
            test_reports=tuple(sorted(test_reports, key=lambda item: item.path)),
            coverage_reports=tuple(sorted(coverage_reports, key=lambda item: item.path)),
            gaps=tuple(gaps),
        )


def _is_junit_or_pytest_report(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/").lower()
    filename = normalized.rsplit("/", maxsplit=1)[-1]
    return (
        filename.endswith(".xml")
        and ("junit" in filename or "pytest" in filename or "test-results" in normalized)
    )


def _parse_test_report(path: Path, file: InventoryFile) -> TestReportSummary | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None
    candidate = root
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
        candidate = root if root.attrib.get("tests") else suites[0] if suites else root
    report_type: TestReportType = "pytest" if "pytest" in file.path.lower() else "junit"
    return TestReportSummary(
        path=file.path,
        report_type=report_type,
        tests=_int_attr(candidate, "tests"),
        failures=_int_attr(candidate, "failures"),
        errors=_int_attr(candidate, "errors"),
        skipped=_int_attr(candidate, "skipped"),
        evidence_id=file.evidence_id,
    )


def _parse_coverage_xml(path: Path, file: InventoryFile) -> CoverageSummary | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None
    line_rate = _float_attr(root, "line-rate")
    lines_valid = _int_attr(root, "lines-valid") or None
    lines_covered = _int_attr(root, "lines-covered") or None
    packages = tuple(
        sorted(
            package.attrib["name"]
            for package in root.findall(".//package")
            if package.attrib.get("name")
        )
    )
    return CoverageSummary(
        path=file.path,
        report_type="coverage_xml",
        line_rate=line_rate,
        lines_covered=lines_covered,
        lines_valid=lines_valid,
        packages=packages,
        evidence_id=file.evidence_id,
    )


def _parse_lcov(path: Path, file: InventoryFile) -> CoverageSummary:
    lines_valid = 0
    lines_covered = 0
    packages: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("SF:"):
            packages.add(str(Path(line.removeprefix("SF:")).parent).replace("\\", "/"))
        elif line.startswith("DA:"):
            lines_valid += 1
            _, hit_count = line.removeprefix("DA:").split(",", maxsplit=1)
            if int(hit_count) > 0:
                lines_covered += 1
    line_rate = lines_covered / lines_valid if lines_valid else None
    return CoverageSummary(
        path=file.path,
        report_type="lcov",
        line_rate=line_rate,
        lines_covered=lines_covered,
        lines_valid=lines_valid,
        packages=tuple(sorted(package for package in packages if package != ".")),
        evidence_id=file.evidence_id,
    )


def _parse_jacoco(path: Path, file: InventoryFile) -> CoverageSummary | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None
    covered = 0
    missed = 0
    for counter in root.findall(".//counter"):
        if counter.attrib.get("type") == "LINE":
            covered += int(counter.attrib.get("covered", "0"))
            missed += int(counter.attrib.get("missed", "0"))
    lines_valid = covered + missed
    packages = tuple(
        sorted(
            package.attrib["name"]
            for package in root.findall(".//package")
            if package.attrib.get("name")
        )
    )
    return CoverageSummary(
        path=file.path,
        report_type="jacoco",
        line_rate=covered / lines_valid if lines_valid else None,
        lines_covered=covered,
        lines_valid=lines_valid,
        packages=packages,
        evidence_id=file.evidence_id,
    )


def _gaps(
    test_sources: tuple[TestSourceFile, ...],
    test_reports: list[TestReportSummary],
    coverage_reports: list[CoverageSummary],
) -> list[str]:
    gaps: list[str] = []
    if not test_sources:
        gaps.append("No test source files detected.")
    if not test_reports:
        gaps.append("No pytest or JUnit test report evidence detected.")
    if not coverage_reports:
        gaps.append("No coverage report evidence detected.")
    return gaps


def _int_attr(node: ET.Element, name: str) -> int:
    try:
        return int(float(node.attrib.get(name, "0")))
    except ValueError:
        return 0


def _float_attr(node: ET.Element, name: str) -> float | None:
    try:
        return float(node.attrib[name])
    except (KeyError, ValueError):
        return None
