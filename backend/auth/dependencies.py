"""
Auth Dependencies - FastAPI Depends() for authentication and authorization.

Key design: When AUTH_ENABLED=false (default), get_current_user() returns an
anonymous user with ADMIN_TECHNIQUE role. All existing routes work unchanged.
All 94 existing tests pass without modification.
"""

import logging
from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, Request, status

from auth import AUTH_ENABLED
from auth.schemas import CurrentUser

logger = logging.getLogger(__name__)


def _extract_bearer_token(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_user(request: Request) -> CurrentUser:
    """
    FastAPI dependency: resolve the current user from JWT or return anonymous.

    When AUTH_ENABLED=false:
        Returns anonymous user with ADMIN_TECHNIQUE role (backward compatible).

    When AUTH_ENABLED=true:
        Validates JWT Bearer token and extracts user info + roles from claims.
        Raises 401 if no valid token.
    """
    if not AUTH_ENABLED:
        return CurrentUser(
            sub="anonymous",
            username="anonymous",
            email=None,
            roles=["ADMIN_TECHNIQUE"],
            is_anonymous=True,
        )

    # AUTH_ENABLED=true: validate JWT
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        from auth.jwt_validator import validate_token

        claims = await validate_token(token)
    except Exception as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract roles from claims (Keycloak: realm_access.roles)
    from auth.config import get_oidc_config

    config = get_oidc_config()
    roles = _extract_roles(claims, config.role_claim)

    # Check break-glass status
    break_glass_active = False
    try:
        from auth.break_glass import is_break_glass_active

        user_sub = claims.get("sub", "")
        break_glass_active = is_break_glass_active(user_sub)
    except ImportError:
        pass

    return CurrentUser(
        sub=claims.get("sub", "unknown"),
        username=claims.get("preferred_username", claims.get("sub", "unknown")),
        email=claims.get("email"),
        roles=roles,
        is_anonymous=False,
        break_glass_active=break_glass_active,
    )


def _extract_roles(claims: dict, role_claim: str) -> List[str]:
    """
    Extract roles from JWT claims using dot-notation path.

    Examples:
        - Keycloak: "realm_access.roles" → claims["realm_access"]["roles"]
        - Azure AD: "roles" → claims["roles"]
    """
    parts = role_claim.split(".")
    value = claims
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, [])
        else:
            return []

    if isinstance(value, list):
        # Filter to valid roles only
        valid = {"LECTURE_SEULE", "INFIRMIER", "MEDECIN", "ADMIN_TECHNIQUE"}
        return [r for r in value if r in valid]

    return []


def require_role(*allowed_roles: str) -> Callable:
    """
    FastAPI dependency factory: require specific roles.

    Usage:
        @router.post("/endpoint")
        async def endpoint(user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE"))):
            ...

    When AUTH_ENABLED=false, always passes (anonymous has ADMIN_TECHNIQUE).
    When AUTH_ENABLED=true, raises 403 if user lacks required role.
    Break-glass users get temporary ADMIN_TECHNIQUE access.
    """

    async def _check_role(
        current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
    ) -> CurrentUser:
        if not AUTH_ENABLED:
            return current_user

        # Break-glass grants temporary elevated access
        if current_user.break_glass_active:
            return current_user

        if not current_user.has_role(*allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(allowed_roles)}. "
                f"Your roles: {', '.join(current_user.roles)}",
            )
        return current_user

    return _check_role
