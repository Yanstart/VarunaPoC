"""
Authentication/Authorization Exceptions
"""

from .base import VarunaError


class AuthenticationError(VarunaError):
    """Base exception for authentication errors."""
    pass


class AuthorizationError(VarunaError):
    """Base exception for authorization errors."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when JWT/OAuth token expired."""

    def __init__(self):
        super().__init__(
            message="Token expired",
            user_message="Votre session a expiré. Veuillez vous reconnecter."
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""

    def __init__(self):
        super().__init__(
            message="Invalid credentials",
            user_message="Identifiants incorrects. Veuillez réessayer."
        )
