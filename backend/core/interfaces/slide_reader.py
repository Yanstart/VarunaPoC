"""
Slide Reader Protocol

Resource-style Protocol for slide readers. Stateful by design: an instance
represents an open slide with a clear lifecycle (open / read many regions /
close). This shape is mandated by the WSI domain — opening a multi-gigapixel
slide is expensive (file descriptor, OpenSlide native init), so the cost
must be amortized across many tile reads.

Contrast with the Service-style Protocols (AuthProvider, StorageProvider,
TileCache, WorkflowHook) which are stateless and take resource identifiers
on each call.

This Protocol replaces the previously cherry-picked stateless `SlideLoader`
Protocol (a29a46a), which did not match the project's existing reader
architecture (selector.py + ISlideReader ABC) and would have ruined tile
serving performance if adopted as-is.

References:
- PEP 544: Protocols (structural subtyping)
- docs/architecture/READER_SELECTION_SYSTEM.md
- docs/architecture/MODULAR_ARCHITECTURE.md (Service vs Resource Protocols)
"""

from typing import TYPE_CHECKING, List, Protocol, Tuple, runtime_checkable

import numpy as np

if TYPE_CHECKING:
    from services.readers.base import SlideMetadata


@runtime_checkable
class SlideReader(Protocol):
    """
    Stateful Protocol for slide readers.

    Lifecycle:
        1. Instantiate: reader = OpenSlideReader()
        2. Open file:   reader.open("/path/to/slide.svs")
        3. Use:         region = reader.read_region(...)
        4. Close:       reader.close()

    Or use as context manager:
        >>> with OpenSlideReader() as reader:
        ...     reader.open("/path/to/slide.svs")
        ...     meta = reader.get_metadata()

    Class methods `supported_formats()` and `can_open()` are used by
    ReaderSelector to choose the best reader for a given file.

    Implementations:
        - OpenSlideReader (svs, ndpi, mrxs, bif, scn, tif/tiff, vms, vmu)
        - BioFormatsReader (extended formats via Bio-Formats)
        - OMETIFFReader (OME-TIFF)
        - OMEZarrReader (OME-Zarr / NGFF)

    Why Protocol instead of ABC?
        - PEP 544 structural subtyping: implementations don't need to inherit
        - Easier to mock in tests
        - Aligns with the project's other Protocols (auth, storage, etc.)
        - @runtime_checkable enables isinstance() checks for the registry
    """

    def open(self, path: str) -> None:
        """Open a slide file for reading.

        Args:
            path: Absolute path to the slide file.

        Raises:
            FileNotFoundError: If the file does not exist.
            RuntimeError: If the file cannot be opened by this reader.
        """
        ...

    def close(self) -> None:
        """Close the slide and release resources.

        Safe to call multiple times. After close(), all other methods
        except open() will raise RuntimeError.
        """
        ...

    def read_region(
        self, location: Tuple[int, int], level: int, size: Tuple[int, int]
    ) -> np.ndarray:
        """Read a region from the slide.

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

    def get_metadata(self) -> "SlideMetadata":
        """Extract metadata from the open slide.

        Returns:
            SlideMetadata dataclass with all available information.

        Raises:
            RuntimeError: If slide is not open.
        """
        ...

    def get_thumbnail(self, size: Tuple[int, int]) -> np.ndarray:
        """Get a thumbnail image of the slide.

        Args:
            size: Maximum (width, height). Aspect ratio is preserved.

        Returns:
            numpy array with shape (height, width, 3) in RGB format, dtype uint8.

        Raises:
            RuntimeError: If slide is not open.
        """
        ...

    @property
    def dimensions(self) -> Tuple[int, int]:
        """Slide dimensions (width, height) at level 0."""
        ...

    @property
    def level_count(self) -> int:
        """Number of pyramid levels."""
        ...

    @property
    def level_dimensions(self) -> List[Tuple[int, int]]:
        """List of (width, height) for each pyramid level."""
        ...


__all__ = ["SlideReader"]
