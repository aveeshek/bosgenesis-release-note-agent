"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DEFAULT_APP_NAME = "bosgenesis-release-note-agent"
DEFAULT_ENVIRONMENT = "local"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "json"
DEFAULT_API_HOST = "0.0.0.0"
DEFAULT_API_PORT = 8080
DEFAULT_MCP_HOST = "0.0.0.0"
DEFAULT_MCP_PORT = 8090
DEFAULT_WORKSPACE_ROOT = Path("data/workspaces")
DEFAULT_ARTIFACT_ROOT = Path("data/artifacts")
DEFAULT_JOB_ROOT = Path("data/jobs")
DEFAULT_LOG_ROOT = Path("data/logs")
DEFAULT_MAX_REPO_SIZE_MB = 500
DEFAULT_MAX_FILE_SIZE_MB = 10
DEFAULT_CLONE_TIMEOUT_SECONDS = 120
DEFAULT_ANALYSIS_TIMEOUT_SECONDS = 600
DEFAULT_LANGFUSE_ENDPOINT = "http://langfuse-web.bosgenesis.svc.cluster.local:3000"
DEFAULT_OTLP_ENDPOINT = "http://signoz-otel-collector.signoz.svc.cluster.local:4317"
DEFAULT_OLLAMA_BASE_URL = "http://ollama.bosgenesis.svc.cluster.local:11434"
DEFAULT_OLLAMA_MODEL = "gemma4:26b"
DEFAULT_MCP_ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "release-note-agent.bosgenesis.local",
    "bosgenesis-release-note-agent-mcp",
    "bosgenesis-release-note-agent-mcp.bosgenesis.svc",
    "bosgenesis-release-note-agent-mcp.bosgenesis.svc.cluster.local",
]


def _get_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    return int(raw_value)


def _get_path(name: str, default: str) -> Path:
    return Path(os.getenv(name, default)).expanduser()


def _get_csv(name: str, default: list[str]) -> list[str]:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    return [item.strip() for item in raw_value.split(",") if item.strip()]


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Runtime configuration shared by API, MCP, CLI, and worker modes."""

    app_name: str = DEFAULT_APP_NAME
    environment: str = DEFAULT_ENVIRONMENT
    log_level: str = DEFAULT_LOG_LEVEL
    log_format: str = DEFAULT_LOG_FORMAT
    enable_rest_api: bool = True
    enable_mcp_server: bool = True
    enable_cli: bool = True
    api_host: str = DEFAULT_API_HOST
    api_port: int = DEFAULT_API_PORT
    mcp_host: str = DEFAULT_MCP_HOST
    mcp_port: int = DEFAULT_MCP_PORT
    mcp_allowed_hosts: list[str] | None = None
    workspace_root: Path = DEFAULT_WORKSPACE_ROOT
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT
    job_root: Path = DEFAULT_JOB_ROOT
    log_root: Path = DEFAULT_LOG_ROOT
    max_repo_size_mb: int = DEFAULT_MAX_REPO_SIZE_MB
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB
    clone_timeout_seconds: int = DEFAULT_CLONE_TIMEOUT_SECONDS
    analysis_timeout_seconds: int = DEFAULT_ANALYSIS_TIMEOUT_SECONDS
    database_url: str | None = None
    redis_url: str | None = None
    enable_otel: bool = False
    enable_langfuse: bool = False
    langfuse_endpoint: str = DEFAULT_LANGFUSE_ENDPOINT
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    otlp_endpoint: str = DEFAULT_OTLP_ENDPOINT
    enable_observability_audit: bool = True
    enable_observability_phase_metrics: bool = True
    enable_observability_warning_taxonomy: bool = True
    enable_llm_summary: bool = False
    enable_llm_reasoning: bool = False
    llm_default_model: str = DEFAULT_OLLAMA_MODEL
    llm_provider: str = "ollama"
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    llm_temperature: float = 0.2
    llm_max_tokens: int = 900
    llm_minimum_confidence: float = 0.85
    enable_pdf_rendering: bool = True

    @classmethod
    def from_env(cls) -> AppConfig:
        """Build configuration from `GRNA_*` environment variables."""

        return cls(
            app_name=os.getenv("GRNA_APP_NAME", DEFAULT_APP_NAME),
            environment=os.getenv("GRNA_ENVIRONMENT", DEFAULT_ENVIRONMENT),
            log_level=os.getenv("GRNA_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            log_format=os.getenv("GRNA_LOG_FORMAT", DEFAULT_LOG_FORMAT).lower(),
            enable_rest_api=_get_bool("GRNA_ENABLE_REST_API", True),
            enable_mcp_server=_get_bool("GRNA_ENABLE_MCP_SERVER", True),
            enable_cli=_get_bool("GRNA_ENABLE_CLI", True),
            api_host=os.getenv("GRNA_API_HOST", DEFAULT_API_HOST),
            api_port=_get_int("GRNA_API_PORT", DEFAULT_API_PORT),
            mcp_host=os.getenv("GRNA_MCP_HOST", DEFAULT_MCP_HOST),
            mcp_port=_get_int("GRNA_MCP_PORT", DEFAULT_MCP_PORT),
            mcp_allowed_hosts=_get_csv("GRNA_MCP_ALLOWED_HOSTS", DEFAULT_MCP_ALLOWED_HOSTS),
            workspace_root=_get_path("GRNA_WORKSPACE_ROOT", str(DEFAULT_WORKSPACE_ROOT)),
            artifact_root=_get_path("GRNA_ARTIFACT_ROOT", str(DEFAULT_ARTIFACT_ROOT)),
            job_root=_get_path("GRNA_JOB_ROOT", str(DEFAULT_JOB_ROOT)),
            log_root=_get_path("GRNA_LOG_ROOT", str(DEFAULT_LOG_ROOT)),
            max_repo_size_mb=_get_int("GRNA_MAX_REPO_SIZE_MB", DEFAULT_MAX_REPO_SIZE_MB),
            max_file_size_mb=_get_int("GRNA_MAX_FILE_SIZE_MB", DEFAULT_MAX_FILE_SIZE_MB),
            clone_timeout_seconds=_get_int(
                "GRNA_CLONE_TIMEOUT_SECONDS",
                DEFAULT_CLONE_TIMEOUT_SECONDS,
            ),
            analysis_timeout_seconds=_get_int(
                "GRNA_ANALYSIS_TIMEOUT_SECONDS",
                DEFAULT_ANALYSIS_TIMEOUT_SECONDS,
            ),
            database_url=os.getenv("GRNA_DATABASE_URL") or None,
            redis_url=os.getenv("GRNA_REDIS_URL") or None,
            enable_otel=_get_bool("GRNA_ENABLE_OTEL", False),
            enable_langfuse=_get_bool("GRNA_ENABLE_LANGFUSE", False),
            langfuse_endpoint=os.getenv("LANGFUSE_HOST", DEFAULT_LANGFUSE_ENDPOINT),
            langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY") or None,
            langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY") or None,
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", DEFAULT_OTLP_ENDPOINT),
            enable_observability_audit=_get_bool("OBSERVABILITY_AUDIT_ENABLED", True),
            enable_observability_phase_metrics=_get_bool(
                "OBSERVABILITY_PHASE_METRICS_ENABLED",
                True,
            ),
            enable_observability_warning_taxonomy=_get_bool(
                "OBSERVABILITY_WARNING_TAXONOMY_ENABLED",
                True,
            ),
            enable_llm_summary=_get_bool("GRNA_ENABLE_LLM_SUMMARY", False),
            enable_llm_reasoning=_get_bool(
                "GRNA_ENABLE_LLM_REASONING",
                _get_bool("GRNA_ENABLE_LLM_SUMMARY", False),
            ),
            llm_default_model=os.getenv("GRNA_LLM_DEFAULT_MODEL")
            or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            llm_provider=os.getenv("GRNA_LLM_PROVIDER", "ollama"),
            ollama_base_url=os.getenv("GRNA_OLLAMA_BASE_URL")
            or os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
            llm_temperature=float(os.getenv("GRNA_LLM_TEMPERATURE", "0.2")),
            llm_max_tokens=_get_int("GRNA_LLM_MAX_TOKENS", 900),
            llm_minimum_confidence=float(os.getenv("GRNA_LLM_MINIMUM_CONFIDENCE", "0.85")),
            enable_pdf_rendering=_get_bool(
                "GRNA_ENABLE_PDF_RENDERING",
                True,
            ),
        )


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Return cached application configuration."""

    return AppConfig.from_env()


def reset_config_cache() -> None:
    """Clear cached configuration, mainly for tests."""

    get_config.cache_clear()
