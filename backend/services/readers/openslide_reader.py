"""
OpenSlide Reader

Adapter wrapping the OpenSlide library to implement the ISlideReader interface.
This is the primary reader for most whole-slide image formats.

Supported formats:
- Aperio SVS (.svs)
- Hamamatsu NDPI (.ndpi)
- 3DHistech MIRAX (.mrxs)
- Ventana BIF (.bif)
- Leica SCN (.scn)
- Generic pyramidal TIFF (.tif, .tiff)

References:
- OpenSlide: https://openslide.org/
- OpenSlide Python API: https://openslide.org/api/python/
- Existing usage: services/tile_server.py
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from .base import ISlideReader, SlideMetadata

logger = logging.getLogger(__name__)

# Supported file extensions and their confidence scores
_OPENSLIDE_FORMATS: dict[str, int] = {
    "svs": 90,
    "ndpi": 90,
    "mrxs": 90,
    "bif": 90,
    "scn": 90,
    "tif": 80,
    "tiff": 80,
    "vms": 90,
    "vmu": 90,
    "svslide": 90,
}


class OpenSlideReader(ISlideReader):
    """
    Slide reader backed by OpenSlide.

    Wraps ``openslide.OpenSlide`` to conform to the ISlideReader ABC.
    Converts RGBA output from OpenSlide to RGB numpy arrays.

    Examples:
        >>> with OpenSlideReader() as reader:
        ...     reader.open("/path/to/slide.svs")
        ...     print(reader.dimensions)
        ...     region = reader.read_region((0, 0), 0, (256, 256))
    """

    def __init__(self) -> None:
        self._slide: Optional[object] = None
        self._path: Optional[str] = None

    def open(self, path: str) -> None:
        """Open a slide file with OpenSlide."""
        import openslide

        if not Path(path).exists():
            raise FileNotFoundError(f"Slide not found: {path}")

        try:
            self._slide = openslide.OpenSlide(path)
            self._path = path
            logger.info(f"OpenSlideReader opened: {Path(path).name}")
        except Exception as e:
            raise RuntimeError(f"OpenSlide cannot open {path}: {e}") from e

    def close(self) -> None:
        """Close the slide and release resources."""
        if self._slide is not None:
            self._slide.close()
            self._slide = None
            self._path = None

    def read_region(
        self, location: Tuple[int, int], level: int, size: Tuple[int, int]
    ) -> np.ndarray:
        """Read a region and return as RGB numpy array."""
        if self._slide is None:
            raise RuntimeError("Slide not open")

        # OpenSlide returns RGBA PIL Image
        pil_image = self._slide.read_region(location, level, size)
        # Convert RGBA to RGB
        rgb_image = pil_image.convert("RGB")
        return np.array(rgb_image)

    def get_metadata(self) -> SlideMetadata:
        """Extract metadata from the open slide."""
        if self._slide is None:
            raise RuntimeError("Slide not open")

        import openslide

        props = dict(self._slide.properties)
        width, height = self._slide.dimensions

        # Extract microns per pixel
        mpp_x = None
        mpp_y = None
        try:
            mpp_x_str = props.get(openslide.PROPERTY_NAME_MPP_X)
            mpp_y_str = props.get(openslide.PROPERTY_NAME_MPP_Y)
            if mpp_x_str is not None:
                mpp_x = float(mpp_x_str)
            if mpp_y_str is not None:
                mpp_y = float(mpp_y_str)
        except (ValueError, TypeError):
            pass

        # Extract objective power
        objective_power = None
        try:
            obj_str = props.get(openslide.PROPERTY_NAME_OBJECTIVE_POWER)
            if obj_str is not None:
                objective_power = int(float(obj_str))
        except (ValueError, TypeError):
            pass

        vendor = props.get(openslide.PROPERTY_NAME_VENDOR)

        return SlideMetadata(
            width=width,
            height=height,
            level_count=self._slide.level_count,
            level_dimensions=list(self._slide.level_dimensions),
            mpp_x=mpp_x,
            mpp_y=mpp_y,
            objective_power=objective_power,
            vendor=vendor,
            format_name=self._detect_format_name(),
            properties=props,
        )

    def get_thumbnail(self, size: Tuple[int, int]) -> np.ndarray:
        """Get a thumbnail as RGB numpy array."""
        if self._slide is None:
            raise RuntimeError("Slide not open")

        pil_thumb = self._slide.get_thumbnail(size)
        return np.array(pil_thumb.convert("RGB"))

    @property
    def dimensions(self) -> Tuple[int, int]:
        """Slide dimensions (width, height) at level 0."""
        if self._slide is None:
            raise RuntimeError("Slide not open")
        return self._slide.dimensions

    @property
    def level_count(self) -> int:
        """Number of pyramid levels."""
        if self._slide is None:
            raise RuntimeError("Slide not open")
        return self._slide.level_count

    @property
    def level_dimensions(self) -> List[Tuple[int, int]]:
        """Dimensions of each pyramid level."""
        if self._slide is None:
            raise RuntimeError("Slide not open")
        return list(self._slide.level_dimensions)

    def _detect_format_name(self) -> Optional[str]:
        """Detect format name from the open slide."""
        if self._path is None:
            return None
        try:
            import openslide

            return openslide.OpenSlide.detect_format(self._path)
        except Exception:
            return None

    @classmethod
    def supported_formats(cls) -> List[str]:
        """Return list of supported file extensions."""
        return list(_OPENSLIDE_FORMATS.keys())

    @classmethod
    def can_open(cls, path: str) -> int:
        """
        Return confidence score for ability to open this file.

        Checks file extension against known OpenSlide formats.
        Returns 90 for native formats, 80 for generic TIFF, 0 for unknown.
        """
        ext = Path(path).suffix.lower().lstrip(".")
        return _OPENSLIDE_FORMATS.get(ext, 0)
