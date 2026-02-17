"""
ISlideReader Abstract Base Class

Abstract base class defining the interface that ALL slide readers must implement.
Follows the Strategy Pattern to allow interchangeable reader implementations.

Design patterns:
- Strategy Pattern: Each reader is an interchangeable strategy
- Template Method: Context manager support via __enter__/__exit__

References:
- Architecture doc: docs/architecture/READER_SELECTION_SYSTEM.md
- Existing pattern: core/interfaces/ml_provider.py (Protocol/ABC usage)
- OpenSlide API: https://openslide.org/api/python/

Issue #8: ISlideReader ABC
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


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
# ABSTRACT BASE CLASS
# ============================================================================


class ISlideReader(ABC):
    """
    Abstract base class for slide readers.

    All concrete readers (OpenSlide, BioFormats, OME-TIFF, OME-Zarr, etc.)
    must implement this interface.

    Lifecycle:
        1. Instantiate reader: ``reader = OpenSlideReader()``
        2. Open file: ``reader.open("/path/to/slide.svs")``
        3. Use reader: ``region = reader.read_region(...)``
        4. Close: ``reader.close()``

    Or use as context manager:
        >>> with OpenSlideReader() as reader:
        ...     reader.open("/path/to/slide.svs")
        ...     meta = reader.get_metadata()

    Class methods ``supported_formats()`` and ``can_open()`` are used by
    ReaderSelector to choose the best reader for a given file.

    References:
        - docs/architecture/READER_SELECTION_SYSTEM.md
        - core/interfaces/ml_provider.py (Protocol pattern example)
    """

    @abstractmethod
    def open(self, path: str) -> None:
        """
        Open a slide file for reading.

        Args:
            path: Absolute path to the slide file.

        Raises:
            FileNotFoundError: If the file does not exist.
            RuntimeError: If the file cannot be opened by this reader.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """
        Close the slide and release resources.

        Safe to call multiple times. After close(), all other methods
        except open() will raise RuntimeError.
        """
        ...

    @abstractmethod
    def read_region(
        self, location: Tuple[int, int], level: int, size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Read a region from the slide.

        Args:
            location: (x, y) coordinates at level 0 (top-left corner).
            level: Pyramid level (0 = highest resolution).
            size: (width, height) of the region to read at the given level.

        Returns:
            numpy array with shape (height, width, 3) in RGB format, dtype uint8.

        Raises:
            RuntimeError: If slide is not open.
            ValueError: If level or coordinates are out of bounds.
        """
        ...

    @abstractmethod
    def get_metadata(self) -> SlideMetadata:
        """
        Extract metadata from the open slide.

        Returns:
            SlideMetadata dataclass with all available information.

        Raises:
            RuntimeError: If slide is not open.
        """
        ...

    @abstractmethod
    def get_thumbnail(self, size: Tuple[int, int]) -> np.ndarray:
        """
        Get a thumbnail image of the slide.

        Args:
            size: Maximum (width, height). Aspect ratio is preserved.

        Returns:
            numpy array with shape (height, width, 3) in RGB format, dtype uint8.

        Raises:
            RuntimeError: If slide is not open.
        """
        ...

    @property
    @abstractmethod
    def dimensions(self) -> Tuple[int, int]:
        """Slide dimensions (width, height) at level 0."""
        ...

    @property
    @abstractmethod
    def level_count(self) -> int:
        """Number of pyramid levels."""
        ...

    @property
    @abstractmethod
    def level_dimensions(self) -> List[Tuple[int, int]]:
        """List of (width, height) for each pyramid level."""
        ...

    # Context manager support
    def __enter__(self) -> "ISlideReader":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @classmethod
    @abstractmethod
    def supported_formats(cls) -> List[str]:
        """
        Return list of file extensions this reader supports.

        Returns:
            List of lowercase extensions without dots, e.g. ['svs', 'ndpi', 'mrxs'].
        """
        ...

    @classmethod
    @abstractmethod
    def can_open(cls, path: str) -> int:
        """
        Return a confidence score (0-100) for the ability to open a file.

        Used by ReaderSelector to rank readers. Higher score = better match.

        Scoring guidelines:
            - 90-100: Native format, excellent support
            - 70-89: Good support with minor limitations
            - 50-69: Partial support
            - 1-49: Experimental/untested
            - 0: Cannot open this file

        Args:
            path: Path to the slide file.

        Returns:
            Integer confidence score 0-100.
        """
        ...
