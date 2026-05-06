"""
Workflow Integration Exceptions
"""

from .base import VarunaError


class WorkflowError(VarunaError):
    """Base exception for workflow errors."""


class WorklistNotFoundError(WorkflowError):
    """Raised when worklist item not found."""

    def __init__(self, accession_number: str):
        super().__init__(
            message=f"Worklist item not found: {accession_number}",
            details={"accession_number": accession_number},
            user_message=f"L'item worklist '{accession_number}' est introuvable."
        )


class WorkflowIntegrationError(WorkflowError):
    """Raised when external workflow system is unreachable."""

    def __init__(self, system: str, details: str = ""):
        super().__init__(
            message=f"Workflow integration error with {system}: {details}",
            details={"system": system, "error_details": details},
            user_message=f"Erreur de connexion au système {system}. Contactez l'administrateur."
        )
