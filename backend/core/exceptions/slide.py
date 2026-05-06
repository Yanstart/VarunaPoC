"""
Slide-related Exceptions
"""

from .base import VarunaError


class SlideFormatError(VarunaError):
    """Base exception for slide format errors."""


class SlideCorruptedError(SlideFormatError):
    """Raised when slide file is corrupted."""

    def __init__(self, slide_path: str, details: str = ""):
        super().__init__(
            message=f"Slide corrupted: {slide_path}. {details}",
            details={"slide_path": slide_path, "error_details": details},
            user_message="La lame est corrompue et ne peut pas être ouverte."
        )


class UnsupportedFormatError(SlideFormatError):
    """Raised when slide format is not supported."""

    def __init__(self, format: str):
        super().__init__(
            message=f"Unsupported format: {format}",
            details={"format": format},
            user_message=f"Le format '{format}' n'est pas supporté."
        )


class InvalidRegionError(VarunaError):
    """Raised when requested region is out of bounds."""

    def __init__(self, level: int, x: int, y: int, width: int, height: int):
        super().__init__(
            message=f"Invalid region: level={level}, x={x}, y={y}, w={width}, h={height}",
            details={"level": level, "x": x, "y": y, "width": width, "height": height},
            user_message="La région demandée est en dehors des limites de la lame."
        )
