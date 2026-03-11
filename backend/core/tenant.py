"""
Tenant Resolution - Extract tenant_id from request context.

Multi-tenancy support for isolating annotations per hospital/organization.
Tenant is resolved from JWT claims (preferred) or X-Tenant-ID header (fallback).
Defaults to "default" when no tenant information is available.

Usage:
    @router.get("/items")
    async def list_items(tenant_id: str = Depends(get_current_tenant)):
        ...
"""

import logging

from fastapi import Request

logger = logging.getLogger(__name__)

# Default tenant for single-hospital deployments and backward compatibility
DEFAULT_TENANT = "default"

# JWT claim path for tenant (Keycloak custom claim)
TENANT_CLAIM = "tenant_id"


async def get_current_tenant(request: Request) -> str:
    """
    FastAPI dependency: resolve the current tenant from request context.

    Resolution order:
    1. JWT claims (tenant_id field) - preferred for authenticated requests
    2. X-Tenant-ID header - fallback for service-to-service calls
    3. "default" - backward compatible single-tenant mode

    Returns:
        Tenant identifier string (e.g., "chu-ucl-namur", "default").
    """
    # 1. Try JWT claims (if auth is enabled and user is authenticated)
    try:
        from auth import AUTH_ENABLED

        if AUTH_ENABLED:
            from auth.dependencies import get_current_user

            user = await get_current_user(request)
            if not user.is_anonymous:
                # Look for tenant_id in the JWT via raw token claims
                token = _extract_bearer_token(request)
                if token:
                    tenant = _extract_tenant_from_token(token)
                    if tenant:
                        return tenant
    except (ImportError, Exception):
        # Auth module not available or token invalid - continue to fallback
        pass

    # 2. Try X-Tenant-ID header
    header_tenant = request.headers.get("X-Tenant-ID")
    if header_tenant:
        return header_tenant.strip()

    # 3. Default tenant
    return DEFAULT_TENANT


def _extract_bearer_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def _extract_tenant_from_token(token: str) -> str | None:
    """
    Extract tenant_id from JWT claims without full validation.

    Uses the already-validated token to read tenant claim.
    Returns None if claim is not present.
    """
    try:
        import base64
        import json

        # Decode JWT payload (second segment) without verification
        # (token was already validated by auth middleware)
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)
        return claims.get(TENANT_CLAIM)
    except Exception:
        return None
