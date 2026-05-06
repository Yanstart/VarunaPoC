"""
FHIR Configuration — read from environment variables.

Mirrors the pattern from auth/config.py: a frozen dataclass populated by
a `get_fhir_config()` factory. The dataclass is immutable so callers can
cache it without worrying about mid-request mutation.

The `FHIRConfig.is_configured` property is the single source of truth for
"should the FHIRWorkflowHook actually try to talk to a server?". When
FHIR_ENABLED=true but FHIR_BASE_URL is empty, we still treat the
configuration as not-ready and the workflow hook degrades to a no-op.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FHIRConfig:
    """FHIR R4 server configuration from environment variables."""

    enabled: bool = False
    base_url: str = ""
    auth_token: str = ""
    timeout_seconds: float = 10.0
    retry_max_attempts: int = 3
    retry_backoff_seconds: float = 2.0

    # Resource types we expect to be supported by the target server.
    # Used by validate_configuration() to surface coverage gaps.
    expected_resources: tuple = ("DiagnosticReport", "Patient")

    @property
    def is_configured(self) -> bool:
        """True when both the feature flag is on AND a base URL is set."""
        return bool(self.enabled and self.base_url)

    @property
    def metadata_url(self) -> str:
        """FHIR CapabilityStatement endpoint (used by health checks)."""
        return f"{self.base_url.rstrip('/')}/metadata"


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def get_fhir_config() -> FHIRConfig:
    """Build a FHIRConfig snapshot from the current environment.

    Each call re-reads env vars so tests can monkeypatch them between cases.
    Production code should cache the result at startup if the cost matters
    (env reads are cheap, so caching is rarely worth it).
    """
    return FHIRConfig(
        enabled=_read_bool("FHIR_ENABLED", False),
        base_url=os.getenv("FHIR_BASE_URL", "").rstrip("/"),
        auth_token=os.getenv("FHIR_AUTH_TOKEN", ""),
        timeout_seconds=_read_float("FHIR_TIMEOUT_SECONDS", 10.0),
        retry_max_attempts=_read_int("FHIR_RETRY_MAX_ATTEMPTS", 3),
        retry_backoff_seconds=_read_float("FHIR_RETRY_BACKOFF_SECONDS", 2.0),
    )


__all__ = ["FHIRConfig", "get_fhir_config"]
