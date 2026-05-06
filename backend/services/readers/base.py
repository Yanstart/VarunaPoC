"""
Slide Reader Base — Metadata dataclass

This module previously defined an `ISlideReader` ABC. The project has moved
to PEP 544 Protocols for all module interfaces (see core/interfaces/), and
the slide reader contract now lives in `core.interfaces.slide_reader.SlideReader`.

What stays here:
- `SlideMetadata` — the dataclass returned by readers' `get_metadata()`. It
  is colocated with concrete reader implementations because it is purely a
  reader-side concern (format-level technical metadata: dimensions, mpp,
  vendor, etc.) and does not belong in core/interfaces.

For backward compatibility, `ISlideReader` is re-exported as an alias to
the new `SlideReader` Protocol. New code should import `SlideReader`
directly from `core.interfaces.slide_reader`.

References:
- core/interfaces/slide_reader.py (new Protocol)
- docs/architecture/READER_SELECTION_SYSTEM.md
- docs/architecture/MODULAR_ARCHITECTURE.md (Service vs Resource Protocols)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class SlideMetadata:
    """
    Metadata extracted from a slide file.

    Covers both traditional 2D whole-slide images and N-dimensional
    formats (OME-TIFF, OME-Zarr) with channels, Z-levels, and timepoints.

    Attributes:
        width: Slide width at level 0 (pixels)
        height: Slide height at level 0 (pixels)
        level_count: Number of pyramid levels
        level_dimensions: List of (width, height) for each level
        mpp_x: Microns per pixel (X axis), None if unknown
        mpp_y: Microns per pixel (Y axis), None if unknown
        objective_power: Objective magnification (e.g. 20, 40), None if unknown
        vendor: Scanner/instrument vendor name
        format_name: Detected format name (e.g. "aperio", "hamamatsu")
        properties: Raw key-value properties from the reader
        channels: Number of channels (for OME formats, default 1)
        z_levels: Number of Z-stack levels (for OME formats, default 1)
        timepoints: Number of timepoints (for OME formats, default 1)

    Examples:
        >>> meta = SlideMetadata(
        ...     width=100000, height=80000,
        ...     level_count=4,
        ...     level_dimensions=[(100000, 80000), (50000, 40000),
        ...                       (25000, 20000), (12500, 10000)],
        ...     mpp_x=0.25, mpp_y=0.25,
        ...     objective_power=40,
        ...     vendor="Aperio",
        ...     format_name="aperio"
        ... )
    """

    width: int
    height: int
    level_count: int
    level_dimensions: List[Tuple[int, int]]
    mpp_x: Optional[float] = None
    mpp_y: Optional[float] = None
    objective_power: Optional[int] = None
    vendor: Optional[str] = None
    format_name: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)
    # N-dimensional (for OME formats)
    channels: int = 1
    z_levels: int = 1
    timepoints: int = 1


# ============================================================================
# CONCRETE HELPER: SlideReaderBase
# ============================================================================
# A tiny non-abstract base providing the context-manager protocol for slide
# readers. Concrete readers (OpenSlideReader, BioFormatsReader, etc.) inherit
# from it for `with reader: ...` support without re-implementing __enter__/
# __exit__ in every reader.
#
# This is NOT an ABC — it does not enforce method implementations. Conformance
# to the SlideReader Protocol is verified structurally via duck typing
# (PEP 544). Inheriting from SlideReaderBase is purely a code-reuse choice.


class SlideReaderBase:
    """Concrete helper base with context-manager support.

    Subclassing is optional; structural conformance to SlideReader is the
    real contract. Use this base only for the `with` statement convenience.
    """

    def __enter__(self) -> "SlideReaderBase":
        return self

    def __exit__(self, *args: object) -> None:
        # Subclasses must define close()
        self.close()  # type: ignore[attr-defined]


# ============================================================================
# BACKWARD COMPATIBILITY: ISlideReader -> SlideReader Protocol
# ============================================================================
# Existing code uses `from services.readers.base import ISlideReader`.
# Re-export the new Protocol under that name. New code should import
# `SlideReader` from core.interfaces.slide_reader directly.

from core.interfaces.slide_reader import SlideReader as ISlideReader


__all__ = ["SlideMetadata", "SlideReaderBase", "ISlideReader"]
