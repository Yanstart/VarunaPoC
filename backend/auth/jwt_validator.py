"""
JWT Validator - Validate and decode JWT tokens using JWKS.

Supports RS256 and ES256 signing algorithms.
Uses python-jose for JWT decoding and signature verification.
"""

import logging
from typing import Any, Dict

from jose import JWTError, jwt

from auth.config import get_oidc_config
from auth.oidc import find_key_by_kid, get_jwks

logger = logging.getLogger(__name__)


async def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate a JWT token against the OIDC provider's JWKS.

    Steps:
    1. Decode header to get kid (key ID) and algorithm
    2. Fetch JWKS (cached) and find matching key
    3. Verify signature and decode claims
    4. Validate issuer, audience, expiration

    Returns:
        Decoded JWT claims dict.

    Raises:
        ValueError: If token is invalid, expired, or verification fails.
    """
    config = get_oidc_config()

    # Step 1: Decode header (unverified) to get kid
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise ValueError(f"Invalid JWT header: {e}")

    kid = unverified_header.get("kid")
    alg = unverified_header.get("alg", "RS256")

    if alg not in config.algorithms:
        raise ValueError(f"Unsupported algorithm: {alg}")

    # Step 2: Get JWKS and find key
    jwks = await get_jwks(config)
    key = find_key_by_kid(jwks, kid) if kid else None

    # If key not found, try refreshing JWKS (key rotation)
    if key is None and kid:
        logger.info(f"Key {kid} not found in JWKS, refreshing...")
        jwks = await get_jwks(config, force_refresh=True)
        key = find_key_by_kid(jwks, kid)

    if key is None:
        raise ValueError(f"No matching key found for kid={kid}")

    # Step 3: Verify and decode
    try:
        return jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience=config.audience,
            issuer=config.issuer_url,
            options={
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
                "verify_iat": True,
            },
        )
    except JWTError as e:
        raise ValueError(f"JWT verification failed: {e}")
