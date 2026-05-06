"""
PACS Configuration — read from environment variables.

Mirrors the pattern from auth/config.py and fhir/config.py: a frozen
dataclass populated by `get_pacs_config()`. The dataclass is immutable
so callers can cache or share it without race risk.

`PACSConfig.is_configured` is the single source of truth for "should we
actually try to talk DICOM?". When PACS_ENABLED=true but the AE Titles
are empty, the configuration is treated as not-ready and the workflow
hook is skipped (NoOpWorkflowHook is used instead).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PACSConfig:
    """DICOM PACS configuration from environment variables."""

    enabled: bool = False
    host: str = "localhost"
    dicom_port: int = 4242
    http_url: str = ""
    aet_local: str = ""
    aet_remote: str = ""
    http_user: str = ""
    http_password: str = ""
    timeout_seconds: float = 30.0
    retry_max_attempts: int = 2
    retry_backoff_seconds: float = 2.0

    @property
    def is_configured(self) -> bool:
        """True iff the feature flag is on AND both AE Titles are set."""
        return bool(self.enabled and self.aet_local and self.aet_remote)

    @property
    def has_http_fallback(self) -> bool:
        """True iff the Orthanc HTTP REST endpoint is configured.

        update_worklist falls back to HTTP since DICOM has no native
        worklist-update operation. Without an HTTP endpoint the method
        raises NotImplementedError.
        """
        return bool(self.http_url)


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def get_pacs_config() -> PACSConfig:
    """Build a PACSConfig snapshot from the current environment.

    Each call re-reads env vars so tests can monkeypatch them between
    cases without warming a cached instance.
    """
    return PACSConfig(
        enabled=_read_bool("PACS_ENABLED", False),
        host=os.getenv("PACS_HOST", "localhost"),
        dicom_port=_read_int("PACS_DICOM_PORT", 4242),
        http_url=os.getenv("PACS_HTTP_URL", "").rstrip("/"),
        aet_local=os.getenv("PACS_AET_LOCAL", "").strip(),
        aet_remote=os.getenv("PACS_AET_REMOTE", "").strip(),
        http_user=os.getenv("PACS_HTTP_USER", ""),
        http_password=os.getenv("PACS_HTTP_PASSWORD", ""),
        timeout_seconds=_read_float("PACS_TIMEOUT_SECONDS", 30.0),
        retry_max_attempts=_read_int("PACS_RETRY_MAX_ATTEMPTS", 2),
        retry_backoff_seconds=_read_float("PACS_RETRY_BACKOFF_SECONDS", 2.0),
    )


__all__ = ["PACSConfig", "get_pacs_config"]
