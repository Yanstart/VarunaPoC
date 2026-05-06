"""
Reader Selector

Chain of Responsibility pattern for selecting the best slide reader.
Ranks registered readers by their confidence score for a given file
and tries each in order until one succeeds.

Design patterns:
- Chain of Responsibility: Try readers in score order with fallback
- Registry Pattern: Dynamic reader registration

Issue #18: ReaderSelector
References:
- docs/architecture/READER_SELECTION_SYSTEM.md
- Refactoring Guru: Chain of Responsibility
"""

import logging
from typing import List, Type

from core.interfaces.slide_reader import SlideReader

logger = logging.getLogger(__name__)

# Methods/classmethods a reader class must expose to be registerable.
# Validated structurally at register() time (PEP 544 duck typing) since
# isinstance/issubclass on Protocol-with-properties is not supported.
_REQUIRED_READER_API = (
    "open",
    "close",
    "read_region",
    "get_metadata",
    "get_thumbnail",
    "can_open",
    "supported_formats",
)


class NoCompatibleReaderError(Exception):
    """Raised when no registered reader can open a file."""


class ReaderSelector:
    """
    Selects the best slide reader for a given file path.

    Maintains a registry of reader classes. When ``select()`` is called,
    it scores all readers against the file, sorts by confidence, and
    tries each until one succeeds.

    Examples:
        >>> selector = ReaderSelector()
        >>> selector.register(OpenSlideReader)
        >>> selector.register(OMETIFFReader)
        >>> reader = selector.select("/path/to/slide.svs")
        >>> # reader is now an opened OpenSlideReader instance
    """

    def __init__(self) -> None:
        self._readers: List[Type[SlideReader]] = []

    def register(self, reader_cls: Type[SlideReader]) -> None:
        """
        Register a reader class.

        Args:
            reader_cls: A class that conforms structurally to SlideReader.

        Raises:
            TypeError: If reader_cls is not a class or does not expose the
                       required reader API (open, close, read_region, etc.).
        """
        if not isinstance(reader_cls, type):
            raise TypeError(f"{reader_cls!r} must be a class implementing SlideReader")
        missing = [m for m in _REQUIRED_READER_API if not hasattr(reader_cls, m)]
        if missing:
            raise TypeError(
                f"{reader_cls.__name__} is missing required SlideReader members: "
                f"{', '.join(missing)}"
            )
        if reader_cls not in self._readers:
            self._readers.append(reader_cls)
            logger.debug(f"Registered reader: {reader_cls.__name__}")

    def select(self, path: str) -> SlideReader:
        """
        Select the best reader for a file and open it.

        Tries registered readers in descending confidence score order.
        If the highest-scoring reader fails to open the file, falls back
        to the next one.

        Args:
            path: Path to the slide file.

        Returns:
            An opened SlideReader instance ready for use.

        Raises:
            NoCompatibleReaderError: If no reader can open the file.
        """
        # Score all readers
        ranked = sorted(
            [(cls, cls.can_open(path)) for cls in self._readers],
            key=lambda x: x[1],
            reverse=True,
        )

        errors = []
        for cls, score in ranked:
            if score <= 0:
                continue

            logger.info(f"Trying {cls.__name__} (score={score}) for {path}")

            try:
                reader = cls()
                reader.open(path)
                logger.info(f"SUCCESS: Opened with {cls.__name__}")
                return reader
            except Exception as e:
                logger.warning(f"Reader {cls.__name__} failed for {path}: {e}")
                errors.append(f"{cls.__name__} (score={score}): {e}")
                continue

        # Build detailed error message
        if errors:
            error_detail = "\n  ".join(errors)
            raise NoCompatibleReaderError(
                f"No reader can open: {path}\n" f"Attempted readers:\n  {error_detail}"
            )

        raise NoCompatibleReaderError(
            f"No reader can open: {path} " f"(no registered reader supports this format)"
        )


def default_selector() -> ReaderSelector:
    """
    Create a ReaderSelector with all available readers registered.

    Registers readers in order:
    1. OpenSlideReader (primary, most formats)
    2. OMETIFFReader (OME-TIFF specialist)
    3. OMEZarrReader (OME-Zarr specialist)
    4. BioFormatsReader (fallback, requires JRE)

    Returns:
        A ReaderSelector instance with all readers registered.
    """
    from .bioformats_reader import BioFormatsReader
    from .ome_tiff_reader import OMETIFFReader
    from .ome_zarr_reader import OMEZarrReader
    from .openslide_reader import OpenSlideReader

    selector = ReaderSelector()
    selector.register(OpenSlideReader)
    selector.register(OMETIFFReader)
    selector.register(OMEZarrReader)
    selector.register(BioFormatsReader)

    logger.info(
        f"Default selector created with {len(selector._readers)} readers: "
        f"{[r.__name__ for r in selector._readers]}"
    )
    return selector
