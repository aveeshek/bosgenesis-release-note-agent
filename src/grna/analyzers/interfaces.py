"""Interface surface analyzer."""

from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from grna.analyzers.inventory import RepositoryInventory

InterfaceType = Literal[
    "http_route",
    "cli_command",
    "mcp_tool",
    "environment",
    "config",
    "artifact",
]
InterfaceDirection = Literal["inbound", "outbound", "internal"]

ENV_PATTERN = re.compile(r"(?:os\.environ(?:\.get)?|os\.getenv)\(\s*['\"]([A-Z0-9_]+)['\"]")
ARTIFACT_PATH_PATTERN = re.compile(
    r"['\"]([^'\"]*(?:artifact|report|release-note)[^'\"]*)['\"]",
    re.I,
)


@dataclass(frozen=True, slots=True)
class InterfaceFinding:
    """Detected external or operational interface."""

    interface_type: InterfaceType
    name: str
    direction: InterfaceDirection
    evidence_path: str
    confidence: float
    evidence_id: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class InterfaceAnalysis:
    """Interface analyzer result."""

    interfaces: tuple[InterfaceFinding, ...]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return {
            "interfaces": [interface.to_dict() for interface in self.interfaces],
            "recommendations": list(self.recommendations),
        }


class InterfaceAnalyzer:
    """Detect routes, CLI commands, MCP tools, env vars, configs, and artifact paths."""

    def analyze(
        self,
        repository_path: Path | str,
        inventory: RepositoryInventory,
    ) -> InterfaceAnalysis:
        """Return read-only interface inventory."""

        root = Path(repository_path).resolve()
        findings: list[InterfaceFinding] = []
        for file in inventory.files:
            suffix = Path(file.path).suffix.lower()
            if suffix == ".py":
                findings.extend(_analyze_python_file(root / file.path, file.path, file.evidence_id))
            if file.category == "config":
                findings.append(
                    InterfaceFinding(
                        interface_type="config",
                        name=Path(file.path).name,
                        direction="internal",
                        evidence_path=file.path,
                        evidence_id=file.evidence_id,
                        confidence=0.8,
                    )
                )
        findings = _dedupe_findings(findings)
        recommendations = _recommendations(findings)
        return InterfaceAnalysis(
            interfaces=tuple(sorted(findings, key=lambda item: (item.interface_type, item.name))),
            recommendations=tuple(recommendations),
        )


def _analyze_python_file(
    path: Path,
    relative_path: str,
    evidence_id: str | None,
) -> list[InterfaceFinding]:
    content = path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=relative_path)
    findings: list[InterfaceFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            findings.extend(_function_interfaces(node, relative_path, evidence_id))
        if isinstance(node, ast.Call):
            findings.extend(_call_interfaces(node, relative_path, evidence_id))
    findings.extend(_regex_interfaces(content, relative_path, evidence_id))
    return findings


def _function_interfaces(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    relative_path: str,
    evidence_id: str | None,
) -> list[InterfaceFinding]:
    findings: list[InterfaceFinding] = []
    for decorator in node.decorator_list:
        text = ast.unparse(decorator)
        lowered = text.lower()
        if any(f".{method}(" in lowered for method in ("get", "post", "put", "patch", "delete")):
            findings.append(
                InterfaceFinding(
                    interface_type="http_route",
                    name=node.name,
                    direction="inbound",
                    evidence_path=relative_path,
                    evidence_id=evidence_id,
                    confidence=0.9,
                    details={"decorator": text},
                )
            )
        if ".command" in lowered or ".callback" in lowered:
            findings.append(
                InterfaceFinding(
                    interface_type="cli_command",
                    name=node.name,
                    direction="inbound",
                    evidence_path=relative_path,
                    evidence_id=evidence_id,
                    confidence=0.9,
                    details={"decorator": text},
                )
            )
        if ".tool" in lowered or lowered.endswith("tool()"):
            findings.append(
                InterfaceFinding(
                    interface_type="mcp_tool",
                    name=node.name,
                    direction="inbound",
                    evidence_path=relative_path,
                    evidence_id=evidence_id,
                    confidence=0.9,
                    details={"decorator": text},
                )
            )
    return findings


def _call_interfaces(
    node: ast.Call,
    relative_path: str,
    evidence_id: str | None,
) -> list[InterfaceFinding]:
    findings: list[InterfaceFinding] = []
    text = ast.unparse(node)
    for env_name in ENV_PATTERN.findall(text):
        findings.append(
            InterfaceFinding(
                interface_type="environment",
                name=env_name,
                direction="inbound",
                evidence_path=relative_path,
                evidence_id=evidence_id,
                confidence=0.85,
            )
        )
    return findings


def _regex_interfaces(
    content: str,
    relative_path: str,
    evidence_id: str | None,
) -> list[InterfaceFinding]:
    findings = [
        InterfaceFinding(
            interface_type="artifact",
            name=match,
            direction="outbound",
            evidence_path=relative_path,
            evidence_id=evidence_id,
            confidence=0.65,
        )
        for match in ARTIFACT_PATH_PATTERN.findall(content)
        if "/" in match or "." in match
    ]
    for env_name in set(ENV_PATTERN.findall(content)):
        findings.append(
            InterfaceFinding(
                interface_type="environment",
                name=env_name,
                direction="inbound",
                evidence_path=relative_path,
                evidence_id=evidence_id,
                confidence=0.85,
            )
        )
    return findings


def _dedupe_findings(findings: list[InterfaceFinding]) -> list[InterfaceFinding]:
    deduped: dict[tuple[str, str, str], InterfaceFinding] = {}
    for finding in findings:
        key = (finding.interface_type, finding.name, finding.evidence_path)
        current = deduped.get(key)
        if current is None or finding.confidence > current.confidence:
            deduped[key] = finding
    return list(deduped.values())


def _recommendations(findings: list[InterfaceFinding]) -> list[str]:
    present = {finding.interface_type for finding in findings}
    recommendations: list[str] = []
    if "http_route" not in present:
        recommendations.append("No explicit HTTP route contracts detected.")
    if "cli_command" not in present:
        recommendations.append("No explicit CLI command contracts detected.")
    if "mcp_tool" not in present:
        recommendations.append("No explicit MCP tool contracts detected.")
    if "environment" not in present:
        recommendations.append("No environment variable interface usage detected.")
    return recommendations
