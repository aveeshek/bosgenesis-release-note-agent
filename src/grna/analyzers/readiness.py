"""Release readiness analyzer with documentation coverage and security posture."""

from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from grna.analyzers.inventory import InventoryFile, RepositoryInventory
from grna.config import AppConfig
from grna.llm.readiness_reasoning import ReadinessReasoningResult, build_readiness_reasoning

ReadinessDimension = Literal[
    "API contract",
    "Documentation coverage",
    "Security scan",
    "Repository documentation",
    "Testing",
    "Observability",
    "Persistence",
    "Deployment packaging",
]


@dataclass(frozen=True, slots=True)
class DocumentationCoverageSummary:
    """Bare-minimum source documentation coverage."""

    documentable_symbols: int
    documented_symbols: int
    coverage_percent: float
    files_analyzed: int
    files_with_documentation: int
    language_counts: dict[str, int]
    evidence_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SecurityFinding:
    """Sanitized lightweight security scan finding."""

    rule_id: str
    severity: str
    path: str
    line: int
    description: str
    redacted_snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SecurityScanSummary:
    """Bare-minimum security scan posture."""

    score: float
    scanned_files: int
    findings: tuple[SecurityFinding, ...]
    severity_counts: dict[str, int]
    controls: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    gaps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["findings"] = [finding.to_dict() for finding in self.findings]
        payload["controls"] = list(self.controls)
        payload["evidence_paths"] = list(self.evidence_paths)
        payload["gaps"] = list(self.gaps)
        return payload


@dataclass(frozen=True, slots=True)
class ReadinessScore:
    """One report-ready readiness dimension."""

    dimension: ReadinessDimension
    score: float
    deterministic_score: float
    evidence_interpretation: str
    recommended_action: str
    evidence_paths: tuple[str, ...] = ()
    llm_suggested_score: float | None = None
    llm_confidence: float | None = None
    llm_rationale: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReadinessAnalysis:
    """Release readiness analyzer result."""

    scores: tuple[ReadinessScore, ...]
    documentation_coverage: DocumentationCoverageSummary
    security_scan: SecurityScanSummary
    llm_reasoning: ReadinessReasoningResult
    gaps: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scores": [score.to_dict() for score in self.scores],
            "documentation_coverage": self.documentation_coverage.to_dict(),
            "security_scan": self.security_scan.to_dict(),
            "llm_reasoning": self.llm_reasoning.to_dict(),
            "gaps": list(self.gaps),
            "warnings": list(self.warnings),
        }


class ReadinessAnalyzer:
    """Build evidence-driven readiness scores from repository analytics."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def analyze(
        self,
        repository_path: Path | str,
        inventory: RepositoryInventory,
        *,
        technology: Any,
        documentation: Any,
        interfaces: Any,
        test_coverage: Any,
    ) -> ReadinessAnalysis:
        root = Path(repository_path).resolve()
        docs = analyze_documentation_coverage(root, inventory)
        security = analyze_security_scan(root, inventory)
        deterministic = _build_deterministic_scores(
            docs,
            security,
            technology=technology,
            documentation=documentation,
            interfaces=interfaces,
            test_coverage=test_coverage,
        )
        summary = {
            "documentation_coverage": docs.to_dict(),
            "security_scan": {
                **security.to_dict(),
                "findings": [finding.to_dict() for finding in security.findings[:12]],
            },
            "scores": [score.to_dict() for score in deterministic],
        }
        llm_reasoning = build_readiness_reasoning(
            config=self.config,
            deterministic_summary=summary,
        )
        scores = tuple(_apply_llm_reasoning(deterministic, llm_reasoning))
        gaps = tuple(
            gap
            for gap in (
                "No documentable source symbols were detected for documentation coverage."
                if docs.documentable_symbols == 0
                else "",
                *security.gaps,
            )
            if gap
        )
        return ReadinessAnalysis(
            scores=scores,
            documentation_coverage=docs,
            security_scan=security,
            llm_reasoning=llm_reasoning,
            gaps=gaps,
            warnings=llm_reasoning.warnings,
        )


def analyze_documentation_coverage(
    root: Path,
    inventory: RepositoryInventory,
) -> DocumentationCoverageSummary:
    documentable = 0
    documented = 0
    files_analyzed = 0
    files_with_docs = 0
    language_counts: Counter[str] = Counter()
    evidence_paths: list[str] = []

    for file in _source_files(inventory):
        path = root / file.path
        if file.size_bytes > 750_000:
            continue
        suffix = path.suffix.lower()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        files_analyzed += 1
        language = _language_for_suffix(suffix)
        language_counts[language] += 1
        if suffix == ".py":
            file_documentable, file_documented = _python_doc_counts(text)
        else:
            file_documentable, file_documented = _comment_doc_counts(text, suffix)
        documentable += file_documentable
        documented += file_documented
        if file_documented:
            files_with_docs += 1
            evidence_paths.append(file.path)

    coverage = round((documented / documentable) * 100, 1) if documentable else 0.0
    return DocumentationCoverageSummary(
        documentable_symbols=documentable,
        documented_symbols=documented,
        coverage_percent=coverage,
        files_analyzed=files_analyzed,
        files_with_documentation=files_with_docs,
        language_counts=dict(sorted(language_counts.items())),
        evidence_paths=tuple(evidence_paths[:20]),
    )


def analyze_security_scan(root: Path, inventory: RepositoryInventory) -> SecurityScanSummary:
    findings: list[SecurityFinding] = []
    controls: set[str] = set()
    evidence_paths: set[str] = set()
    scanned_files = 0

    for file in inventory.files:
        normalized = file.path.lower()
        filename = normalized.rsplit("/", maxsplit=1)[-1]
        if _security_control_for_path(normalized):
            controls.add(_security_control_for_path(normalized) or "")
            evidence_paths.add(file.path)
        if filename in _LOCKFILES:
            controls.add("dependency lockfile")
            evidence_paths.add(file.path)

        if file.category not in {"source", "test", "config", "ci", "deployment"}:
            continue
        if file.size_bytes > 500_000:
            continue
        path = root / file.path
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned_files += 1
        if normalized.startswith(".github/workflows/") and "codeql" in text.lower():
            controls.add("CodeQL workflow")
            evidence_paths.add(file.path)
        findings.extend(_scan_security_text(file.path, text))

    findings.sort(key=lambda item: (_severity_rank(item.severity), item.path, item.line))
    findings = findings[:80]
    severity_counts = dict(sorted(Counter(finding.severity for finding in findings).items()))
    score = _security_score(findings, controls)
    gaps = []
    if not controls:
        gaps.append(
            "No explicit security controls such as SECURITY.md, CodeQL, "
            "Dependabot, or lockfiles were detected."
        )
    if scanned_files == 0:
        gaps.append("No text files were available for the lightweight security scan.")
    return SecurityScanSummary(
        score=score,
        scanned_files=scanned_files,
        findings=tuple(findings),
        severity_counts=severity_counts,
        controls=tuple(sorted(controls)),
        evidence_paths=tuple(sorted(evidence_paths)[:20]),
        gaps=tuple(gaps),
    )


def _build_deterministic_scores(
    docs: DocumentationCoverageSummary,
    security: SecurityScanSummary,
    *,
    technology: Any,
    documentation: Any,
    interfaces: Any,
    test_coverage: Any,
) -> tuple[ReadinessScore, ...]:
    has_api = any(
        getattr(finding, "interface_type", "") in {"http_route", "mcp_tool"}
        for finding in getattr(interfaces, "interfaces", ())
    )
    doc_inventory_count = len(getattr(documentation, "documents", ()))
    test_sources = len(getattr(test_coverage, "test_sources", ()))
    has_observability = _has_technology(technology, {"OpenTelemetry", "Langfuse", "SigNoz"})
    has_persistence = _has_technology(
        technology,
        {"PostgreSQL", "Redis", "MongoDB", "Qdrant", "ClickHouse", "SQLite"},
    ) or any(
        "database" in getattr(finding, "name", "").lower()
        or "storage" in getattr(finding, "name", "").lower()
        for finding in getattr(interfaces, "interfaces", ())
    )
    has_deploy = _has_technology(technology, {"Docker", "Helm", "Kubernetes"})
    docs_score = _documentation_score(docs, doc_inventory_count)
    security_findings = len(security.findings)

    return (
        ReadinessScore(
            "API contract",
            4.0 if has_api else 2.0,
            4.0 if has_api else 2.0,
            (
                "REST or MCP-style contracts are visible and testable."
                if has_api
                else "No explicit REST or MCP contract was detected."
            ),
            (
                "Add formal API or MCP examples and backward compatibility policy."
                if has_api
                else "Expose routes, CLI contracts, or MCP tools with examples."
            ),
        ),
        ReadinessScore(
            "Documentation coverage",
            docs_score,
            docs_score,
            (
                f"{docs.documented_symbols}/{docs.documentable_symbols} documentable "
                "source symbols include docstrings or Javadoc-style comments "
                f"({docs.coverage_percent}%)."
            ),
            (
                "Add docstrings or Javadoc-style comments to public modules, "
                "classes, functions, and services."
            ),
            docs.evidence_paths,
        ),
        ReadinessScore(
            "Security scan",
            security.score,
            security.score,
            (
                f"Lightweight scan found {security_findings} sanitized finding(s) "
                f"across {security.scanned_files} file(s); controls: "
                f"{_control_summary(security.controls)}."
            ),
            (
                "Review high/medium findings, add CodeQL/Dependabot/SECURITY.md, "
                "and keep secrets out of source."
            ),
            security.evidence_paths,
        ),
        ReadinessScore(
            "Repository documentation",
            4.1 if doc_inventory_count >= 5 else 3.0 if doc_inventory_count else 2.2,
            4.1 if doc_inventory_count >= 5 else 3.0 if doc_inventory_count else 2.2,
            f"{doc_inventory_count} documentation artifact(s) were inventoried.",
            "Keep README, architecture, operational, and module-level specs current.",
        ),
        ReadinessScore(
            "Testing",
            3.4 if test_sources >= 25 else 3.0 if test_sources else 2.0,
            3.4 if test_sources >= 25 else 3.0 if test_sources else 2.0,
            f"{test_sources} test source file(s) were detected.",
            "Publish test reports and coverage artifacts with release evidence.",
        ),
        ReadinessScore(
            "Observability",
            3.2 if has_observability else 2.4,
            3.2 if has_observability else 2.4,
            (
                "Observability technology markers are visible."
                if has_observability
                else "No explicit observability stack marker was detected."
            ),
            "Add trace IDs, spans, metrics, dashboards, and release observability notes.",
        ),
        ReadinessScore(
            "Persistence",
            3.2 if has_persistence else 2.5,
            3.2 if has_persistence else 2.5,
            (
                "Persistence or storage markers are visible."
                if has_persistence
                else "No explicit durable persistence contract was detected."
            ),
            "Document schemas, migrations, backup, and retention expectations.",
        ),
        ReadinessScore(
            "Deployment packaging",
            3.7 if has_deploy else 2.4,
            3.7 if has_deploy else 2.4,
            (
                "Docker, Helm, or Kubernetes packaging is visible."
                if has_deploy
                else "No deployment packaging evidence was detected."
            ),
            "Add production values, probes, limits, and release pipeline artifacts.",
        ),
    )


def _apply_llm_reasoning(
    scores: tuple[ReadinessScore, ...],
    reasoning: ReadinessReasoningResult,
) -> list[ReadinessScore]:
    by_dimension = {finding.dimension: finding for finding in reasoning.findings}
    updated: list[ReadinessScore] = []
    for score in scores:
        finding = by_dimension.get(score.dimension)
        if finding is None:
            updated.append(score)
            continue
        delta = finding.suggested_score - score.deterministic_score
        bounded_delta = max(-0.5, min(0.5, delta * 0.35))
        final_score = round(max(0.0, min(5.0, score.deterministic_score + bounded_delta)), 1)
        updated.append(
            ReadinessScore(
                dimension=score.dimension,
                score=final_score,
                deterministic_score=score.deterministic_score,
                evidence_interpretation=(
                    f"{score.evidence_interpretation} LLM advisory: {finding.rationale}"
                ),
                recommended_action=score.recommended_action,
                evidence_paths=score.evidence_paths,
                llm_suggested_score=finding.suggested_score,
                llm_confidence=finding.confidence,
                llm_rationale=finding.rationale,
            )
        )
    return updated


_DECLARATION_PATTERNS = {
    ".go": re.compile(r"^\s*(?:func|type)\s+(?:\([^)]*\)\s*)?([A-Z_a-z]\w*)", re.MULTILINE),
    ".rs": re.compile(r"^\s*(?:pub\s+)?(?:fn|struct|enum|trait)\s+([A-Z_a-z]\w*)", re.MULTILINE),
    ".php": re.compile(
        r"^\s*(?:public|protected|private|static|\s)*\s*"
        r"(?:class|interface|trait|function)\s+([A-Z_a-z]\w*)",
        re.MULTILINE,
    ),
    "default": re.compile(
        r"^\s*(?:export\s+)?(?:public|private|protected|static|async|final|abstract|\s)*"
        r"(?:class|interface|enum|function|def)\s+([A-Z_a-z]\w*)",
        re.MULTILINE,
    ),
}


_SECURITY_RULES = (
    (
        "secret.private_key",
        "critical",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ),
    ("secret.aws_access_key", "critical", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("secret.github_token", "critical", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    ("secret.slack_token", "critical", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "secret.assignment",
        "high",
        re.compile(
            r"(?i)\b(password|passwd|secret|api[_-]?key|token)\b"
            r"\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"
        ),
    ),
    ("danger.eval", "high", re.compile(r"\b(eval|exec)\s*\(")),
    ("danger.shell_true", "high", re.compile(r"shell\s*=\s*True")),
    (
        "danger.insecure_tls",
        "medium",
        re.compile(
            r"(?i)(verify\s*=\s*false|insecureSkipVerify\s*[:=]\s*true|"
            r"rejectUnauthorized\s*[:=]\s*false)"
        ),
    ),
    ("danger.curl_pipe_shell", "high", re.compile(r"curl\b[^\n|]*\|\s*(?:sh|bash)")),
    ("danger.chmod_777", "medium", re.compile(r"\bchmod\s+777\b")),
    ("danger.pickle_load", "medium", re.compile(r"\bpickle\.loads?\s*\(")),
)

_LOCKFILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "composer.lock",
    "poetry.lock",
    "uv.lock",
    "pipfile.lock",
    "go.sum",
    "cargo.lock",
    "gemfile.lock",
}


def _source_files(inventory: RepositoryInventory) -> list[InventoryFile]:
    return [
        file
        for file in inventory.files
        if file.category == "source" and Path(file.path).suffix.lower() in _SUPPORTED_DOC_EXTENSIONS
    ]


_SUPPORTED_DOC_EXTENSIONS = {
    ".py",
    ".java",
    ".kt",
    ".scala",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".php",
    ".go",
    ".rs",
    ".cs",
    ".c",
    ".cc",
    ".cpp",
}


def _python_doc_counts(text: str) -> tuple[int, int]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0, 0
    documentable = 0
    documented = 0
    if ast.get_docstring(tree):
        documented += 1
    if any(
        isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        for node in tree.body
    ):
        documentable += 1
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_"):
            continue
        documentable += 1
        if ast.get_docstring(node):
            documented += 1
    return documentable, min(documented, documentable)


def _comment_doc_counts(text: str, suffix: str) -> tuple[int, int]:
    pattern = _DECLARATION_PATTERNS.get(suffix, _DECLARATION_PATTERNS["default"])
    lines = text.splitlines()
    matches = list(pattern.finditer(text))
    documented = 0
    for match in matches:
        line_number = text.count("\n", 0, match.start())
        if _has_leading_doc_comment(lines, line_number):
            documented += 1
    return len(matches), documented


def _has_leading_doc_comment(lines: list[str], declaration_line_index: int) -> bool:
    lookback = lines[max(0, declaration_line_index - 8) : declaration_line_index]
    compact = "\n".join(line.strip() for line in lookback if line.strip())
    return any(marker in compact for marker in ("/**", "///", "'''", '"""')) or bool(
        re.search(r"(?m)^\s*//\s+\S", compact)
    )


def _scan_security_text(relative_path: str, text: str) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if _is_comment_only(line):
            continue
        for rule_id, severity, pattern in _SECURITY_RULES:
            if pattern.search(line):
                findings.append(
                    SecurityFinding(
                        rule_id=rule_id,
                        severity=severity,
                        path=relative_path,
                        line=index,
                        description=_rule_description(rule_id),
                        redacted_snippet=_redact_line(line),
                    )
                )
    return findings


def _security_score(findings: list[SecurityFinding], controls: set[str]) -> float:
    score = 3.0 + min(1.2, len(controls) * 0.25)
    for finding in findings:
        if finding.severity == "critical":
            score -= 1.2
        elif finding.severity == "high":
            score -= 0.65
        elif finding.severity == "medium":
            score -= 0.25
    return round(max(0.5, min(5.0, score)), 1)


def _documentation_score(docs: DocumentationCoverageSummary, doc_inventory_count: int) -> float:
    if docs.documentable_symbols == 0:
        return 2.0 if doc_inventory_count else 1.5
    coverage_score = 1.5 + (docs.coverage_percent / 100) * 3.1
    inventory_bonus = min(0.4, doc_inventory_count * 0.03)
    return round(max(1.0, min(5.0, coverage_score + inventory_bonus)), 1)


def _has_technology(technology: Any, names: set[str]) -> bool:
    normalized = {name.casefold() for name in names}
    return any(
        getattr(finding, "name", "").casefold() in normalized
        for finding in getattr(technology, "findings", ())
    )


def _security_control_for_path(path: str) -> str | None:
    filename = path.rsplit("/", maxsplit=1)[-1]
    if filename == "security.md":
        return "SECURITY.md"
    if path in {".github/dependabot.yml", ".github/dependabot.yaml"}:
        return "Dependabot"
    if path.startswith(".github/workflows/"):
        return "CI workflow"
    return None


def _severity_rank(severity: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(severity, 4)


def _rule_description(rule_id: str) -> str:
    descriptions = {
        "secret.private_key": "Private key material appears to be present.",
        "secret.aws_access_key": "AWS access key pattern appears to be present.",
        "secret.github_token": "GitHub token pattern appears to be present.",
        "secret.slack_token": "Slack token pattern appears to be present.",
        "secret.assignment": "Secret-like value assignment appears to be present.",
        "danger.eval": "Dynamic code execution call detected.",
        "danger.shell_true": "Subprocess shell execution detected.",
        "danger.insecure_tls": "TLS verification appears to be disabled.",
        "danger.curl_pipe_shell": "Network script is piped directly into a shell.",
        "danger.chmod_777": "World-writable permission command detected.",
        "danger.pickle_load": "Unsafe Python pickle deserialization call detected.",
    }
    return descriptions.get(rule_id, "Security-sensitive pattern detected.")


def _redact_line(line: str) -> str:
    snippet = line.strip()[:220]
    snippet = re.sub(r"(['\"])[^'\"]{8,}\1", r"\1***REDACTED***\1", snippet)
    snippet = re.sub(r"(AKIA)[0-9A-Z]{16}", r"\1***REDACTED***", snippet)
    snippet = re.sub(r"gh[pousr]_[A-Za-z0-9_]{20,}", "gh_***REDACTED***", snippet)
    snippet = re.sub(r"xox[baprs]-[A-Za-z0-9-]{12,}", "xox-***REDACTED***", snippet)
    return snippet


def _is_comment_only(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith(("#", "//", "*")) and not re.search(
        r"(?i)(password|secret|token|api[_-]?key|private key)",
        stripped,
    )


def _control_summary(controls: tuple[str, ...]) -> str:
    if not controls:
        return "none detected"
    return ", ".join(controls[:5])


def _language_for_suffix(suffix: str) -> str:
    return {
        ".py": "Python",
        ".java": "Java",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".php": "PHP",
        ".go": "Go",
        ".rs": "Rust",
        ".cs": "C#",
        ".c": "C",
        ".cc": "C++",
        ".cpp": "C++",
    }.get(suffix, suffix.lstrip(".").upper() or "Unknown")
