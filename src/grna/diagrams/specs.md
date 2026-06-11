# Diagrams Module Specification

## Intent

Generate editable architecture and analytics diagrams from normalized evidence and analytics.

## Role

- Produce Mermaid-compatible diagram source.
- Generate C4 context, container, and component diagrams.
- Generate deployment topology diagrams when Docker, Kubernetes, Helm, or CI/CD evidence exists.
- Generate interface maps, runtime flows, module relationships, and repository analysis flows.

## Inputs

- Analytics bundle.
- Evidence index.
- Technology and deployment findings.
- Interface and module relationship findings.

## Outputs

- Diagram definitions as text.
- Diagram metadata including type, confidence, evidence IDs, and artifact path.
- Optional rendered image references when rendering is enabled.

## Expected Diagram Types

- Runtime flow.
- Repository analysis flow.
- C4 context.
- C4 container.
- C4 component.
- Deployment topology.
- Interface relationship map.
- Module dependency graph.
- Commit or change timeline when useful.

## Design Rules

- Mermaid source is the source of truth.
- Low-confidence inferred relationships must be marked or omitted.
- Diagrams must remain renderable in Markdown, HTML, and PDF outputs.
- Diagram generation failure must not block Markdown report generation.
- Do not create diagrams that imply unsupported architecture certainty.

