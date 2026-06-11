import json
import logging

import grna
from grna.config import AppConfig
from grna.logging_config import JsonLogFormatter, configure_logging


def test_package_imports_with_version() -> None:
    assert grna.__version__ == "0.1.0"


def test_config_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("GRNA_APP_NAME", "test-agent")
    monkeypatch.setenv("GRNA_API_PORT", "9090")
    monkeypatch.setenv("GRNA_ENABLE_MCP_SERVER", "false")

    config = AppConfig.from_env()

    assert config.app_name == "test-agent"
    assert config.api_port == 9090
    assert config.enable_mcp_server is False


def test_json_formatter_includes_extra_fields() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="grna.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="stage completed",
        args=(),
        exc_info=None,
    )
    record.job_id = "scan_001"
    record.stage = "foundation"

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "stage completed"
    assert payload["job_id"] == "scan_001"
    assert payload["stage"] == "foundation"


def test_configure_logging_sets_root_handler() -> None:
    configure_logging(AppConfig(log_level="INFO", log_format="text"))

    root_logger = logging.getLogger()

    assert root_logger.level == logging.INFO
    assert root_logger.handlers

