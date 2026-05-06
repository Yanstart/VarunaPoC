"""
Storage-related Exceptions
"""

from .base import VarunaError


class StorageError(VarunaError):
    """Base exception for storage errors."""


class SlideNotFoundError(StorageError):
    """Raised when slide cannot be found."""

    def __init__(self, slide_id: str):
        super().__init__(
            message=f"Slide not found: {slide_id}",
            details={"slide_id": slide_id},
            user_message=f"La lame demandée (ID: {slide_id}) est introuvable."
        )


class SlideAccessDeniedError(StorageError):
    """Raised when user lacks permission to access slide."""

    def __init__(self, slide_id: str, user_id: str):
        super().__init__(
            message=f"Access denied to slide {slide_id} for user {user_id}",
            details={"slide_id": slide_id, "user_id": user_id},
            user_message="Vous n'avez pas la permission d'accéder à cette lame."
        )


class StorageQuotaExceededError(StorageError):
    """Raised when storage quota exceeded."""

    def __init__(self, current_size: int, quota: int):
        super().__init__(
            message=f"Storage quota exceeded: {current_size} bytes (quota: {quota} bytes)",
            details={"current_size": current_size, "quota": quota},
            user_message="Le quota de stockage est dépassé. Contactez l'administrateur."
        )
