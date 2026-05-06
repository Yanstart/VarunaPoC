"""
OIDC AuthProvider — Strangler Fig adapter wrapping the existing OIDC stack
(jwt_validator, oidc, dependencies) behind the `AuthProvider` Protocol from
core.interfaces.auth.

Why this exists
---------------
The Protocol-based architecture (see docs/architecture/MODULAR_ARCHITECTURE.md)
defines AuthProvider as the canonical interface between VarunaPoC and any
identity provider (Keycloak today; LDAP / Azure AD / Telemis tomorrow).
This adapter is the first concrete implementer on main: it does not change
behavior, it only exposes the existing OIDC code under the Protocol surface.

Methods implemented today
-------------------------
- validate_token: full delegation to auth.jwt_validator.validate_token,
  then mapping JWT claims -> Protocol User.
- authenticate: when credentials carry a "token" field, delegates to
  validate_token. Username/password authentication is intentionally not
  supported here — Keycloak handles that flow client-side via PKCE.
- authorize: VarunaPoC's RBAC is role-based; checks user.roles against
  the resource:action policy table.

Methods stubbed
---------------
- refresh_token, logout, get_user_by_id: raise NotImplementedError with a
  pointer. These need additional infrastructure (token blacklist DB,
  refresh-token endpoint wiring) that does not exist on main yet. They
  will be added when AuthProvider is wired into the actual login flow.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from auth.config import get_oidc_config
from auth.jwt_validator import validate_token as _jwt_validate_token
from core.exceptions.auth import AuthenticationError
from core.interfaces.auth import User

logger = logging.getLogger(__name__)


# Roles recognized by VarunaPoC (must match auth/dependencies.py:_extract_roles)
_VALID_ROLES = frozenset({"LECTURE_SEULE", "INFIRMIER", "MEDECIN", "ADMIN_TECHNIQUE"})


def _user_from_claims(claims: Dict[str, Any]) -> User:
    """Map JWT claims (Keycloak / Azure AD shape) into a Protocol User.

    Mirrors the logic in auth.dependencies.get_current_user but returns the
    AuthProvider Protocol's `User` rather than the FastAPI-flavoured
    `CurrentUser`. The two coexist during the Strangler Fig migration.
    """
    config = get_oidc_config()

    sub = claims.get("sub", "unknown")
    username = claims.get("preferred_username", sub)
    email = claims.get("email")

    # Walk dotted role-claim path (e.g. "realm_access.roles" for Keycloak).
    parts = config.role_claim.split(".")
    value: Any = claims
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, [])
        else:
            value = []
            break
    raw_roles = value if isinstance(value, list) else []
    roles = [r for r in raw_roles if r in _VALID_ROLES]

    metadata: Dict[str, Any] = {}
    if "iss" in claims:
        metadata["issuer"] = claims["iss"]
    if "aud" in claims:
        metadata["audience"] = claims["aud"]
    if "exp" in claims:
        metadata["exp"] = claims["exp"]

    return User(
        user_id=sub,
        username=username,
        email=email,
        roles=roles,
        metadata=metadata,
    )


# Resource:action -> required roles. Centralises the RBAC policy that today
# is scattered across `require_role(...)` decorators on routes. New code
# should consult this table via authorize(); legacy decorators stay in place
# until each route is migrated.
_AUTHORIZATION_MATRIX: Dict[str, Dict[str, frozenset]] = {
    "slide": {
        "read": frozenset({"LECTURE_SEULE", "INFIRMIER", "MEDECIN", "ADMIN_TECHNIQUE"}),
        "annotate": frozenset({"MEDECIN", "ADMIN_TECHNIQUE"}),
        "delete": frozenset({"ADMIN_TECHNIQUE"}),
    },
    "annotation": {
        "read": frozenset({"INFIRMIER", "MEDECIN", "ADMIN_TECHNIQUE"}),
        "create": frozenset({"MEDECIN", "ADMIN_TECHNIQUE"}),
        "validate": frozenset({"MEDECIN", "ADMIN_TECHNIQUE"}),
        "delete": frozenset({"MEDECIN", "ADMIN_TECHNIQUE"}),
    },
    "ml": {
        "inference": frozenset({"MEDECIN", "ADMIN_TECHNIQUE"}),
        "train": frozenset({"ADMIN_TECHNIQUE"}),
    },
    "admin": {
        "configure": frozenset({"ADMIN_TECHNIQUE"}),
        "audit": frozenset({"ADMIN_TECHNIQUE"}),
    },
}


class OIDCAuthProvider:
    """AuthProvider Protocol implementer wrapping the existing OIDC stack.

    Stateless: a single instance can serve every request. Wired as a
    singleton via `get_auth_provider()`.
    """

    async def authenticate(self, credentials: Dict[str, Any]) -> User | None:
        """Authenticate via a JWT bearer token carried in `credentials["token"]`.

        VarunaPoC delegates the username/password flow to Keycloak (PKCE).
        By the time the API receives a request, the client already holds a
        token; authentication here means "validate this token and resolve
        the user." If you call this with anything else, it returns None.
        """
        token = credentials.get("token")
        if not isinstance(token, str) or not token:
            return None
        try:
            return await self.validate_token(token)
        except AuthenticationError:
            return None

    async def authorize(self, user: User, resource: str, action: str) -> bool:
        """Check whether `user` may perform `action` on `resource`.

        Resource is a kind ("slide", "annotation", "ml", "admin"), not a
        specific id. Per-instance ACL (e.g. slide:abc123 owned by user X)
        is intentionally out of scope for the Protocol; routes that need
        ownership checks layer them on top of this allow/deny.
        """
        if not user.roles:
            return False
        kind = resource.split(":", 1)[0] if ":" in resource else resource
        rules = _AUTHORIZATION_MATRIX.get(kind)
        if rules is None:
            # Unknown resource kind: deny by default. Loud log so the policy
            # gap is visible in staging before it bites in production.
            logger.warning(
                "authorize() called with unknown resource kind %r (action=%r); denying",
                kind,
                action,
            )
            return False
        allowed = rules.get(action)
        if allowed is None:
            logger.warning(
                "authorize() called with unknown action %r on %r; denying", action, kind
            )
            return False
        return any(role in allowed for role in user.roles)

    async def validate_token(self, token: str) -> User | None:
        """Validate a JWT and return the Protocol User, or None if invalid."""
        try:
            claims = await _jwt_validate_token(token)
        except ValueError as e:
            # jwt_validator raises ValueError on signature / expiry / kid mismatch.
            logger.info("Token validation failed: %s", e)
            raise AuthenticationError(
                f"Invalid token: {e}",
                details={"reason": str(e)},
            ) from e
        return _user_from_claims(claims)

    async def refresh_token(self, refresh_token: str) -> str | None:
        """Not yet implemented — see module docstring."""
        msg = (
            "refresh_token requires wiring auth/oidc.py to the Keycloak token "
            "endpoint. Track in a follow-up commit when the refresh flow is added."
        )
        raise NotImplementedError(msg)

    async def logout(self, user: User, token: str | None = None) -> bool:
        """Not yet implemented — needs a token-blacklist table on PostgreSQL."""
        msg = (
            "logout requires a token blacklist table. Track in a follow-up "
            "commit when the blacklist is added (or when sessions move to a "
            "stateful session store)."
        )
        raise NotImplementedError(msg)

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Not yet implemented — needs a users table or directory query.

        VarunaPoC currently treats Keycloak as the source of truth; there is
        no internal users table to query. When break-glass / audit features
        need user lookup, add this against the audit_user_cache table.
        """
        msg = (
            "get_user_by_id requires a directory or cache table. Track in a "
            "follow-up commit when the lookup target is decided."
        )
        raise NotImplementedError(msg)


# ---------------------------------------------------------------------------
# Singleton wiring
# ---------------------------------------------------------------------------

_singleton: OIDCAuthProvider | None = None


def get_auth_provider() -> OIDCAuthProvider:
    """Return the process-wide OIDCAuthProvider instance.

    Stateless instance: cheap to share. Lazily created so that import order
    and test isolation are not constrained.
    """
    global _singleton
    if _singleton is None:
        _singleton = OIDCAuthProvider()
    return _singleton


__all__ = ["OIDCAuthProvider", "get_auth_provider"]
