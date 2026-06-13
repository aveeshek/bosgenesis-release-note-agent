"""Mermaid diagram generation from analytics bundles."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

from grna.evidence.aggregator import AnalyticsBundle

DiagramType = Literal[
    "repository_analysis_flow",
    "c4_context",
    "c4_container",
    "component",
    "deployment_topology",
]


@dataclass(frozen=True, slots=True)
class MermaidDiagram:
    """Mermaid source plus report metadata."""

    diagram_id: str
    diagram_type: DiagramType
    title: str
    caption: str
    source: str
    confidence: float
    evidence_ids: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        payload = asdict(self)
        payload["evidence_ids"] = list(self.evidence_ids)
        payload["gaps"] = list(self.gaps)
        return payload


@dataclass(frozen=True, slots=True)
class MermaidDiagramSet:
    """Generated Mermaid diagrams for one analytics bundle."""

    diagrams: tuple[MermaidDiagram, ...]
    gaps: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible data."""

        return {
            "diagrams": [diagram.to_dict() for diagram in self.diagrams],
            "gaps": list(self.gaps),
        }

    def by_type(self, diagram_type: DiagramType) -> MermaidDiagram | None:
        """Return a diagram by type."""

        for diagram in self.diagrams:
            if diagram.diagram_type == diagram_type:
                return diagram
        return None


class MermaidDiagramGenerator:
    """Generate Mermaid diagrams without implying unsupported certainty."""

    def generate(self, bundle: AnalyticsBundle) -> MermaidDiagramSet:
        """Generate all currently supported diagrams from analytics."""

        diagrams = [
            self.repository_analysis_flow(bundle),
            self.c4_context(bundle),
            self.c4_container(bundle),
            self.component(bundle),
        ]
        deployment = self.deployment_topology(bundle)
        gaps: list[str] = []
        if deployment is None:
            gaps.append("Deployment topology diagram unavailable: no deployment evidence detected.")
        else:
            diagrams.append(deployment)
        return MermaidDiagramSet(diagrams=tuple(diagrams), gaps=tuple(gaps))

    def repository_analysis_flow(self, bundle: AnalyticsBundle) -> MermaidDiagram:
        """Generate the repository analysis pipeline diagram."""

        source = "\n".join(
            [
                "flowchart LR",
                "  repo[GitHub Repository]",
                "  fetch[Repository Fetcher]",
                "  inventory[Inventory Analyzer]",
                "  evidence[Evidence Index]",
                "  analyzers[Analyzer Suite]",
                "  analytics[Analytics Bundle]",
                "  report[Release Note]",
                (
                    "  repo --> fetch --> inventory --> evidence --> analyzers "
                    "--> analytics --> report"
                ),
            ]
        )
        return MermaidDiagram(
            diagram_id="diagram_repository_analysis_flow",
            diagram_type="repository_analysis_flow",
            title="Repository Analysis Flow",
            caption="Repository evidence is collected before analytics and report rendering.",
            source=source,
            confidence=0.95,
            evidence_ids=bundle.evidence_ids,
        )

    def c4_context(self, bundle: AnalyticsBundle) -> MermaidDiagram:
        """Generate a C4-style context diagram using Mermaid flowchart syntax."""

        repo_name = _repo_label(bundle)
        source = "\n".join(
            [
                "flowchart TB",
                "  user[Reviewer]",
                f"  repo[{_node_text(repo_name)}]",
                "  agent[BOS Genesis Release Note Agent]",
                "  artifacts[Markdown / HTML / PDF Artifacts]",
                "  user -->|provides GitHub URL| agent",
                "  agent -->|reads public code and metadata| repo",
                "  agent -->|generates| artifacts",
                "  user -->|reviews| artifacts",
            ]
        )
        return MermaidDiagram(
            diagram_id="diagram_c4_context",
            diagram_type="c4_context",
            title="C4 Context",
            caption="High-level context for repository scanning and release-note production.",
            source=source,
            confidence=0.8,
            evidence_ids=bundle.evidence_ids,
        )

    def c4_container(self, bundle: AnalyticsBundle) -> MermaidDiagram:
        """Generate a container-level diagram for the agent runtime."""

        source = "\n".join(
            [
                "flowchart TB",
                "  api[REST API]",
                "  mcp[MCP Server]",
                "  worker[Analyzer Worker]",
                "  storage[(Local Job and Artifact Store)]",
                "  github[Public GitHub Repository]",
                "  api --> storage",
                "  mcp --> storage",
                "  api --> worker",
                "  mcp --> worker",
                "  worker --> github",
                "  worker --> storage",
            ]
        )
        return MermaidDiagram(
            diagram_id="diagram_c4_container",
            diagram_type="c4_container",
            title="C4 Container",
            caption="Runtime containers and their main data flows.",
            source=source,
            confidence=0.75,
            evidence_ids=_section_evidence(bundle, "interfaces"),
        )

    def component(self, bundle: AnalyticsBundle) -> MermaidDiagram:
        """Generate a component diagram from available analyzer sections."""

        component_names = [
            "inventory",
            "technology",
            "documentation",
            "commits",
            "code_structure",
            "interfaces",
            "test_coverage",
        ]
        lines = ["flowchart LR", "  evidence[Evidence Index]", "  bundle[Analytics Bundle]"]
        for name in component_names:
            if name in bundle.sections:
                node_id = _node_id(name)
                lines.append(f"  {node_id}[{_node_text(name.replace('_', ' ').title())}]")
                lines.append(f"  evidence --> {node_id} --> bundle")
        if len(lines) == 2:
            lines.append("  evidence --> bundle")
        return MermaidDiagram(
            diagram_id="diagram_component",
            diagram_type="component",
            title="Component Analysis",
            caption="Analyzer components feeding the normalized analytics bundle.",
            source="\n".join(lines),
            confidence=0.85 if len(lines) > 3 else 0.45,
            evidence_ids=bundle.evidence_ids,
        )

    def deployment_topology(self, bundle: AnalyticsBundle) -> MermaidDiagram | None:
        """Generate deployment topology when deployment evidence exists."""

        technology = bundle.sections.get("technology")
        if technology is None:
            return None
        findings = technology.data.get("findings", [])
        names = {str(finding.get("name", "")).lower() for finding in findings}
        deployment_nodes = [
            expected
            for expected in ("docker", "helm", "kubernetes", "github actions")
            if expected in names
        ]
        if not deployment_nodes:
            return None

        lines = ["flowchart TB", "  repo[Repository]", "  ci[CI/CD]"]
        if "github actions" in deployment_nodes:
            lines.append("  repo --> ci")
        if "docker" in deployment_nodes:
            lines.extend(["  image[Docker Image]", "  ci --> image"])
        if "helm" in deployment_nodes:
            lines.extend(["  chart[Helm Chart]", "  image --> chart"])
        if "kubernetes" in deployment_nodes:
            upstream = "chart" if "helm" in deployment_nodes else "image"
            lines.extend(["  cluster[Kubernetes Cluster]", f"  {upstream} --> cluster"])
        return MermaidDiagram(
            diagram_id="diagram_deployment_topology",
            diagram_type="deployment_topology",
            title="Deployment Topology",
            caption="Deployment topology derived only from detected deployment evidence.",
            source="\n".join(lines),
            confidence=0.8,
            evidence_ids=technology.evidence_ids,
        )


def _repo_label(bundle: AnalyticsBundle) -> str:
    inventory = bundle.sections.get("inventory")
    if inventory:
        root_path = inventory.data.get("root_path")
        if root_path:
            return str(root_path).replace("\\", "/").rstrip("/").rsplit("/", maxsplit=1)[-1]
    return "Target Repository"


def _section_evidence(bundle: AnalyticsBundle, section_name: str) -> tuple[str, ...]:
    section = bundle.sections.get(section_name)
    return section.evidence_ids if section else ()


def _node_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value) or "node"


def _node_text(value: str) -> str:
    return value.replace("[", "(").replace("]", ")")
