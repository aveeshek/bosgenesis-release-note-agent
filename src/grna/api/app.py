"""FastAPI application factory for the REST API runtime."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from grna.config import get_config


def create_app() -> FastAPI:
    """Create the REST API app.

    Full scan APIs are introduced in the API task. Health endpoints are available now so
    deployments can probe the container.
    """

    config = get_config()
    app = FastAPI(title=config.app_name, version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy", "service": config.app_name}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready", "service": config.app_name}

    return app


def main() -> None:
    """Run the REST API with Uvicorn."""

    config = get_config()
    uvicorn.run(
        "grna.api.app:create_app",
        factory=True,
        host=config.api_host,
        port=config.api_port,
    )


if __name__ == "__main__":
    main()
