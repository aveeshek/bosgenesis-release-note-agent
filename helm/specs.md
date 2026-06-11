# Helm Specification

## Intent

Store Kubernetes deployment charts for the release-note agent.

## Role

- Define deployable API, MCP, worker, Redis/Valkey, PostgreSQL integration, and artifact storage resources.
- Support namespace-scoped deployment for BOS Genesis environments.
- Configure resource limits, probes, environment variables, and persistent storage.

## Inputs

- Container image references.
- Values for database, queue, artifact storage, ingress, resources, and observability.

## Outputs

- Kubernetes manifests rendered from Helm templates.
- Deployments, services, config maps, secrets references, PVCs, and optional ingress.

## Design Rules

- Do not store secrets directly in chart defaults.
- Expose health and readiness probes.
- Separate API, MCP, and worker deployments where practical.
- Artifact storage must be persistent.
- Values must allow disabling optional observability integrations.

