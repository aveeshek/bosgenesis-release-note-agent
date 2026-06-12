# GitHub Release Note Agent Chart Specification

## Intent

Define the concrete Helm chart for deploying this agent.

## Role

- Own chart templates and values once Kubernetes deployment work starts.
- Deploy REST API, MCP server, worker, queue, storage, and supporting configuration.

## Inputs

- Chart values.
- Container images.
- External PostgreSQL and Redis/Valkey endpoints or bundled development dependencies.

## Outputs

- Kubernetes resources for the GitHub Release Note Intelligence Agent.

## Expected Resources

- API deployment and service.
- MCP deployment and service.
- Worker deployment.
- ConfigMap for non-secret configuration.
- Secret references for database and optional provider credentials.
- PVC or object-storage configuration for artifacts.
- ServiceAccount and RBAC where needed.

## Design Rules

- Chart must be usable for local/dev and production-like environments with separate values.
- Health probes must align with API and MCP runtime endpoints.
- Resource requests and limits must be configurable.
- Secret values must be referenced, not embedded.

