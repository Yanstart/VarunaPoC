"""
OIDC Discovery - Fetch and cache provider configuration + JWKS.

Implements OpenID Connect Discovery 1.0:
- Fetches .well-known/openid-configuration
- Caches JWKS (JSON Web Key Set) with configurable TTL
- Supports key rotation (re-fetches on unknown kid)
"""

import logging
import time
from typing import Any

import httpx

from auth.config import OIDCConfig, get_oidc_config

logger = logging.getLogger(__name__)

# Cached OIDC discovery and JWKS
_discovery_cache: dict[str, Any] | None = None
_discovery_cache_time: float = 0
_jwks_cache: dict[str, Any] | None = None
_jwks_cache_time: float = 0


async def get_discovery(config: OIDCConfig | None = None) -> dict[str, Any]:
    """
    Fetch and cache OIDC discovery document.

    Returns the full .well-known/openid-configuration response.
    Cached for the configured TTL.
    """
    global _discovery_cache, _discovery_cache_time

    if config is None:
        config = get_oidc_config()

    now = time.time()
    if _discovery_cache and (now - _discovery_cache_time) < config.jwks_cache_ttl:
        return _discovery_cache

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(config.discovery_url)
            response.raise_for_status()
            _discovery_cache = response.json()
            _discovery_cache_time = now
            logger.info(f"OIDC discovery fetched from {config.discovery_url}")
            return _discovery_cache
    except Exception as e:
        logger.error(f"Failed to fetch OIDC discovery: {e}")
        if _discovery_cache:
            logger.warning("Using stale OIDC discovery cache")
            return _discovery_cache
        raise


async def get_jwks(config: OIDCConfig | None = None, force_refresh: bool = False) -> dict[str, Any]:
    """
    Fetch and cache JWKS (JSON Web Key Set).

    The JWKS contains the public keys used to verify JWT signatures.
    Cached with TTL, but can be force-refreshed on unknown kid.
    """
    global _jwks_cache, _jwks_cache_time

    if config is None:
        config = get_oidc_config()

    now = time.time()
    if _jwks_cache and not force_refresh and (now - _jwks_cache_time) < config.jwks_cache_ttl:
        return _jwks_cache

    discovery = await get_discovery(config)
    jwks_uri = discovery.get("jwks_uri")
    if not jwks_uri:
        msg = "No jwks_uri in OIDC discovery document"
        raise ValueError(msg)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(jwks_uri)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_time = now
            key_count = len(_jwks_cache.get("keys", []))
            logger.info(f"JWKS fetched: {key_count} keys from {jwks_uri}")
            return _jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        if _jwks_cache:
            logger.warning("Using stale JWKS cache")
            return _jwks_cache
        raise


def find_key_by_kid(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    """Find a specific key in JWKS by key ID (kid)."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


def clear_cache():
    """Clear all cached OIDC data (for testing)."""
    global _discovery_cache, _discovery_cache_time, _jwks_cache, _jwks_cache_time
    _discovery_cache = None
    _discovery_cache_time = 0
    _jwks_cache = None
    _jwks_cache_time = 0
