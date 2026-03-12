"""Structured logging configuration.

When LOG_FORMAT=json (default in production), outputs JSON lines suitable
for log aggregation (ELK, Datadog, Splunk). When LOG_FORMAT=text, uses
standard Python format for human readability during development.
"""

import logging
import os
import sys

_LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()
_LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()


class JSONFormatter(logging.Formatter):
    """Simple JSON log formatter without external dependencies."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import UTC, datetime

        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request_id from contextvars if available
        try:
            from core.request_context import get_request_id

            request_id = get_request_id()
            if request_id:
                log_entry["request_id"] = request_id
        except ImportError:
            pass

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_logging():
    """Configure logging based on LOG_FORMAT env var."""
    root_logger = logging.getLogger()
    root_logger.setLevel(_LOG_LEVEL)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    if _LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
