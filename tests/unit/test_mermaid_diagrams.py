from grna.diagrams import MermaidDiagramGenerator
from grna.evidence import AnalyticsBundle, AnalyticsSection


def test_mermaid_generator_outputs_required_diagrams_with_metadata() -> None:
    bundle = _bundle(with_deployment=True)

    diagrams = MermaidDiagramGenerator().generate(bundle)

    assert diagrams.gaps == ()
    assert diagrams.by_type("repository_analysis_flow").source == "\n".join(
        [
            "flowchart LR",
            "  repo[GitHub Repository]",
            "  fetch[Repository Fetcher]",
            "  inventory[Inventory Analyzer]",
            "  evidence[Evidence Index]",
            "  analyzers[Analyzer Suite]",
            "  analytics[Analytics Bundle]",
            "  report[Release Note]",
            "  repo --> fetch --> inventory --> evidence --> analyzers --> analytics --> report",
        ]
    )
    assert diagrams.by_type("c4_context").caption
    assert diagrams.by_type("c4_context").confidence > 0
    assert diagrams.by_type("deployment_topology").source.startswith("flowchart TB")
    assert "cluster[Kubernetes Cluster]" in diagrams.by_type("deployment_topology").source


def test_mermaid_generator_handles_missing_deployment_evidence() -> None:
    bundle = _bundle(with_deployment=False)

    diagrams = MermaidDiagramGenerator().generate(bundle)

    assert diagrams.by_type("deployment_topology") is None
    assert diagrams.gaps == (
        "Deployment topology diagram unavailable: no deployment evidence detected.",
    )
    assert all(diagram.source.startswith("flowchart ") for diagram in diagrams.diagrams)


def test_mermaid_diagram_serialization_is_json_ready() -> None:
    diagrams = MermaidDiagramGenerator().generate(_bundle(with_deployment=True))

    payload = diagrams.to_dict()

    assert payload["diagrams"][0]["diagram_id"] == "diagram_repository_analysis_flow"
    assert isinstance(payload["diagrams"][0]["evidence_ids"], list)
    assert isinstance(payload["gaps"], list)


def _bundle(with_deployment: bool) -> AnalyticsBundle:
    findings = [
        {
            "name": "Python",
            "category": "language",
            "confidence": 0.95,
            "evidence_ids": ["ev_py"],
        }
    ]
    if with_deployment:
        findings.extend(
            [
                {"name": "Docker", "category": "container", "confidence": 0.95},
                {"name": "Helm", "category": "deployment", "confidence": 0.95},
                {"name": "Kubernetes", "category": "deployment", "confidence": 0.9},
                {"name": "GitHub Actions", "category": "ci", "confidence": 0.95},
            ]
        )
    return AnalyticsBundle(
        job_id="job_diagram",
        generated_at="2026-06-13T00:00:00+00:00",
        sections={
            "inventory": AnalyticsSection(
                name="inventory",
                data={"root_path": "C:/tmp/example"},
                evidence_ids=("ev_inventory",),
            ),
            "technology": AnalyticsSection(
                name="technology",
                data={"findings": findings},
                evidence_ids=("ev_py", "ev_deploy"),
            ),
            "interfaces": AnalyticsSection(
                name="interfaces",
                data={"interfaces": []},
                evidence_ids=("ev_interface",),
            ),
        },
        gaps=(),
        warnings=(),
        evidence_ids=("ev_inventory", "ev_py", "ev_deploy", "ev_interface"),
    )
