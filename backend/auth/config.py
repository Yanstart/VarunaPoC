"""
OIDC Configuration - Reads from environment variables.

Supports any OIDC-compliant IdP (Keycloak dev, Azure AD prod, Imprivata).
Changing OIDC_ISSUER_URL is sufficient to switch IdP.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OIDCConfig:
    """OIDC provider configuration from environment variables."""

    issuer_url: str = ""
    client_id: str = "varuna-viewer"
    # PKCE flow: no client secret needed for public clients
    audience: str = "varuna-viewer"
    # Role claim path in JWT (Keycloak: realm_access.roles, Azure AD: roles)
    role_claim: str = "realm_access.roles"
    # JWKS cache TTL in seconds
    jwks_cache_ttl: int = 3600
    # Supported signing algorithms
    algorithms: tuple = ("RS256", "ES256")
    # Valid roles (ordered by privilege level)
    valid_roles: tuple = ("LECTURE_SEULE", "INFIRMIER", "MEDECIN", "ADMIN_TECHNIQUE")

    @property
    def discovery_url(self) -> str:
        """OpenID Connect discovery endpoint."""
        return f"{self.issuer_url.rstrip('/')}/.well-known/openid-configuration"

    @property
    def is_configured(self) -> bool:
        """Check if OIDC is properly configured."""
        return bool(self.issuer_url and self.client_id)


def get_oidc_config() -> OIDCConfig:
    """Build OIDCConfig from environment variables."""
    return OIDCConfig(
        issuer_url=os.getenv("OIDC_ISSUER_URL", "http://localhost:8180/realms/varuna"),
        client_id=os.getenv("OIDC_CLIENT_ID", "varuna-viewer"),
        audience=os.getenv("OIDC_AUDIENCE", "varuna-viewer"),
        role_claim=os.getenv("OIDC_ROLE_CLAIM", "realm_access.roles"),
        jwks_cache_ttl=int(os.getenv("OIDC_JWKS_CACHE_TTL", "3600")),
    )
