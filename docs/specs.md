# Documentation Specification

## Intent

Store user-facing, operator-facing, and architecture documentation for the GitHub Release Note Intelligence Agent.

## Role

- Explain how to run the agent in API, MCP, CLI, and worker modes.
- Document architecture, contracts, deployment, configuration, and operations.
- Preserve implementation decisions and module responsibilities.

## Inputs

- Source specifications.
- API and MCP contracts.
- Deployment manifests.
- Operational runbooks.

## Outputs

- Architecture documents.
- API and MCP contract documentation.
- Deployment guides.
- Runbooks.
- Troubleshooting guides.

## Design Rules

- Documentation must match implemented behavior.
- Generated examples should be kept small and reproducible.
- Security limitations and missing-evidence behavior must be clear.
- Public docs must not include local secrets or environment-specific credentials.

