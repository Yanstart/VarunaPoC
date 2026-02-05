"""
Authentication Provider Interface

CRITICAL DESIGN PRINCIPLE:
VarunaPoC does NOT implement its own user management system.
Each institution (hospital, university, clinic) has its own:
- LDAP (Lightweight Directory Access Protocol)
- Active Directory (Microsoft AD)
- SSO (Single Sign-On via SAML, OAuth2, OpenID Connect)
- PACS-integrated authentication (Telemis, etc.)

This interface allows VarunaPoC to integrate with ANY authentication system
without modifying core code.

Examples of implementations:
- LDAPAuthProvider (CHU UCL Namur)
- KeycloakAuthProvider (open-source SSO)
- TelemisAuthProvider (PACS integration)
- MockAuthProvider (development/testing)

References:
- LDAP: https://ldap.com/
- OAuth2: https://oauth.net/2/
- OpenID Connect: https://openid.net/connect/
"""

from typing import Protocol, Optional, Dict, Any
from datetime import datetime


class User:
    """
    Minimal user representation.
    Different auth providers may return additional fields.
    """
    def __init__(
        self,
        user_id: str,
        username: str,
        email: Optional[str] = None,
        roles: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.roles = roles or []
        self.metadata = metadata or {}


class AuthProvider(Protocol):
    """
    Protocol for pluggable authentication providers.

    Design Pattern: Strategy Pattern
    Allows runtime selection of authentication strategy.

    Why Protocol instead of ABC?
    - Less coupling (no inheritance required)
    - Duck typing with type checking (structural subtyping)
    - Easier to mock in tests

    Implementation Example:
        >>> class LDAPAuthProvider:
        ...     async def authenticate(self, credentials):
        ...         # Connect to LDAP server
        ...         # Validate credentials
        ...         # Return User object
        ...         pass
        ...     async def authorize(self, user, resource, action):
        ...         # Check LDAP groups for permissions
        ...         pass
    """

    async def authenticate(
        self,
        credentials: Dict[str, Any]
    ) -> Optional[User]:
        """
        Authenticate user with provided credentials.

        Args:
            credentials: Dict containing auth info. Common keys:
                - "username" + "password" (basic auth)
                - "token" (JWT, OAuth token)
                - "certificate" (X.509 cert for mutual TLS)
                - "saml_assertion" (SAML SSO)

        Returns:
            User object if authentication successful, None otherwise

        Examples:
            >>> # Basic auth
            >>> user = await provider.authenticate({
            ...     "username": "pathologist1",
            ...     "password": "secret123"  # pragma: allowlist secret
            ... })

            >>> # JWT token
            >>> user = await provider.authenticate({
            ...     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            ... })

        Notes:
            - MUST NOT store passwords in plain text
            - SHOULD rate-limit authentication attempts
            - SHOULD log authentication events (audit trail)
        """
        ...

    async def authorize(
        self,
        user: User,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if user is authorized to perform action on resource.

        Args:
            user: Authenticated user
            resource: Resource identifier (e.g., "slide:123", "ml_service")
            action: Action to perform (e.g., "read", "write", "delete", "annotate")

        Returns:
            True if authorized, False otherwise

        Examples:
            >>> # Check if user can view slide
            >>> authorized = await provider.authorize(
            ...     user=user,
            ...     resource="slide:abc123",
            ...     action="read"
            ... )

            >>> # Check if user can trigger ML inference
            >>> authorized = await provider.authorize(
            ...     user=user,
            ...     resource="ml_service",
            ...     action="inference"
            ... )

        Authorization Models:
            - RBAC (Role-Based Access Control): Check user.roles
            - ABAC (Attribute-Based): Check user.metadata attributes
            - ACL (Access Control List): Check per-resource permissions
        """
        ...

    async def validate_token(
        self,
        token: str
    ) -> Optional[User]:
        """
        Validate JWT/OAuth token and return user.

        Args:
            token: JWT token string

        Returns:
            User if token valid, None if expired/invalid

        Notes:
            - MUST verify token signature
            - MUST check expiration (exp claim)
            - SHOULD check issuer (iss claim)
            - SHOULD check audience (aud claim)
        """
        ...

    async def refresh_token(
        self,
        refresh_token: str
    ) -> Optional[str]:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            New access token if refresh successful, None otherwise

        Notes:
            - Refresh tokens typically have longer expiration
            - SHOULD rotate refresh tokens (one-time use)
        """
        ...

    async def logout(
        self,
        user: User,
        token: Optional[str] = None
    ) -> bool:
        """
        Logout user (invalidate token/session).

        Args:
            user: User to logout
            token: Token to invalidate (optional)

        Returns:
            True if logout successful

        Notes:
            - SHOULD blacklist token (if stateless JWT)
            - SHOULD clear session (if stateful)
            - SHOULD log logout event (audit trail)
        """
        ...

    async def get_user_by_id(
        self,
        user_id: str
    ) -> Optional[User]:
        """
        Retrieve user by ID (for session restoration, etc.).

        Args:
            user_id: Unique user identifier

        Returns:
            User object if found, None otherwise
        """
        ...
