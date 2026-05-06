"""
Base Exceptions
"""


class VarunaError(Exception):
    """
    Base exception for all VarunaPoC errors.

    All custom exceptions MUST inherit from this.
    Allows catching all VarunaPoC errors with single except clause.
    """

    def __init__(
        self,
        message: str,
        details: dict = None,
        user_message: str = None
    ):
        self.message = message
        self.details = details or {}
        self.user_message = user_message or message
        super().__init__(self.message)


class ConfigurationError(VarunaError):
    """
    Raised when configuration is invalid or missing.

    Examples:
    - Missing environment variable
    - Invalid YAML syntax
    - Contradictory settings
    """


class ValidationError(VarunaError):
    """
    Raised when input validation fails.

    Examples:
    - Invalid slide_id format
    - Out-of-range coordinates
    - Missing required fields
    """
