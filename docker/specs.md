# Docker Specification

## Intent

Define containerization assets for local development and deployment of the API, MCP server, and worker processes.

## Role

- Store Dockerfile-related assets when code implementation begins.
- Support repeatable local and CI builds.
- Support API, MCP, and worker runtime profiles.

## Inputs

- Python package source.
- Dependency lock or project metadata.
- Runtime configuration.

## Outputs

- Container images.
- Optional compose support for PostgreSQL, Redis, API, MCP, and worker services.

## Design Rules

- Containers must not run scanned repository code by default.
- Build layers should separate dependencies from source where practical.
- Runtime user should be non-root where possible.
- Workspace and artifact paths must be mounted or configured explicitly.

