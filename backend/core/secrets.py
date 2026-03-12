"""
Secrets resolution — Docker Secrets with environment variable fallback.

Priority order:
1. Docker Secret file at /run/secrets/{name} (production)
2. Environment variable os.getenv(name, default) (dev / CI)

Usage:
    from backend.core.secrets import get_secret

    db_password = get_secret("db_password")
    redis_password = get_secret("redis_password", default="")

References:
    - Docker Secrets documentation:
      https://docs.docker.com/engine/swarm/secrets/
    - Docker Compose secrets:
      https://docs.docker.com/compose/use-secrets/
"""

import os
from pathlib import Path

_SECRETS_DIR = Path("/run/secrets")


def get_secret(name: str, default: str | None = None) -> str | None:
    """
    Resolve a secret by name.

    Reads from /run/secrets/{name} if the file exists (Docker Secrets),
    otherwise falls back to os.getenv(name, default).

    Args:
        name: Secret name (matches both the file basename and env var name).
        default: Value returned when neither source is available.

    Returns:
        Secret value as a stripped string, or default.
    """
    secret_path = _SECRETS_DIR / name
    try:
        return secret_path.read_text().strip()
    except OSError:
        return os.getenv(name, default)
