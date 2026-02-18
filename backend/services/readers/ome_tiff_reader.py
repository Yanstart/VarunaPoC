"""
OME-TIFF Reader

Implements ISlideReader for OME-TIFF files using the tifffile library.
OME-TIFF is an open standard for microscopy image data with embedded
OME-XML metadata describing channels, Z-stacks, and timepoints.

This reader:
- Uses tifffile (pure Python, no JRE needed)
- Reads pyramid levels from sub-IFDs or series
- Parses OME-XML metadata for channels, Z, T dimensions
- Falls back gracefully if tifffile is not installed
- Populates SlideMetadata including N-dimensional fields

Supported formats:
- .ome.tiff / .ome.tif (OME-TIFF standard)

Issue #40: OME-TIFF Reader
References:
- OME-TIFF specification: https://docs.openmicroscopy.org/ome-model/latest/ome-tiff/
- tifffile: https://github.com/cgohlke/tifffile
"""

import contextlib
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple
from xml.etree import ElementTree as ET

import numpy as np

from .base import ISlideReader, SlideMetadata

logger = logging.getLogger(__name__)

# Try to import optional dependency
_HAS_TIFFFILE = False
try:
    import tifffile

    _HAS_TIFFFILE = True
except ImportError:
    tifffile = None  # type: ignore[assignment]


def _is_ome_tiff(path: str) -> bool:
    """
    Check if a TIFF file contains OME-XML in its description tag.

    Reads only the first page's description to avoid loading the entire file.
    Returns False if tifffile is not installed or file is not OME-TIFF.
    """
    if not _HAS_TIFFFILE:
        return False

    try:
        with tifffile.TiffFile(path) as tif:
            if not tif.pages:
                return False
            desc = tif.pages[0].description or ""
            # OME-TIFF files have OME-XML starting with <OME or containing OME namespace
            return desc.strip().startswith("<?xml") and "ome" in desc.lower()
    except Exception:
        return False


def _parse_ome_xml(xml_string: str) -> dict:
    """
    Parse OME-XML to extract dimensional metadata.

    Returns dict with keys: channels, z_levels, timepoints, mpp_x, mpp_y.
    """
    result: dict = {
        "channels": 1,
        "z_levels": 1,
        "timepoints": 1,
        "mpp_x": None,
        "mpp_y": None,
    }

    try:
        # Strip namespace for simpler parsing
        xml_clean = re.sub(r'\sxmlns="[^"]+"', "", xml_string, count=1)
        root = ET.fromstring(xml_clean)

        # Find Pixels element
        pixels = root.find(".//Pixels")
        if pixels is not None:
            size_c = pixels.get("SizeC")
            size_z = pixels.get("SizeZ")
            size_t = pixels.get("SizeT")
            physical_x = pixels.get("PhysicalSizeX")
            physical_y = pixels.get("PhysicalSizeY")

            if size_c is not None:
                result["channels"] = int(size_c)
            if size_z is not None:
                result["z_levels"] = int(size_z)
            if size_t is not None:
                result["timepoints"] = int(size_t)
            if physical_x is not None:
                result["mpp_x"] = float(physical_x)
            if physical_y is not None:
                result["mpp_y"] = float(physical_y)
    except Exception as e:
        logger.warning(f"Failed to parse OME-XML: {e}")

    return result


class OMETIFFReader(ISlideReader):
    """
    Slide reader for OME-TIFF files using tifffile.

    Reads pyramid levels and OME-XML metadata. Supports multi-channel,
    multi-Z, and multi-timepoint datasets.

    Examples:
        >>> reader = OMETIFFReader()
        >>> reader.open("/path/to/slide.ome.tiff")
        >>> meta = reader.get_metadata()
        >>> print(f"Channels: {meta.channels}, Z: {meta.z_levels}")
    """

    def __init__(self) -> None:
        self._tif: Optional[object] = None
        self._path: Optional[str] = None
        self._levels: List[object] = []
        self._ome_meta: dict = {}

    def open(self, path: str) -> None:
        """Open an OME-TIFF file."""
        if not _HAS_TIFFFILE:
            raise RuntimeError(
                "OMETIFFReader requires the tifffile package. " "Install with: pip install tifffile"
            )

        if not Path(path).exists():
            raise FileNotFoundError(f"Slide not found: {path}")

        try:
            tif = tifffile.TiffFile(path)

            # Extract OME-XML metadata
            if tif.pages:
                desc = tif.pages[0].description or ""
                if "ome" in desc.lower():
                    self._ome_meta = _parse_ome_xml(desc)

            # Detect pyramid levels from series
            if tif.series:
                self._levels = list(tif.series)
            else:
                self._levels = []

            self._tif = tif
            self._path = path
            logger.info(f"OMETIFFReader opened: {Path(path).name}")
        except Exception as e:
            raise RuntimeError(f"Cannot open OME-TIFF {path}: {e}") from e

    def close(self) -> None:
        """Close the OME-TIFF file."""
        if self._tif is not None:
            with contextlib.suppress(Exception):
                self._tif.close()  # type: ignore[union-attr]
            self._tif = None
            self._path = None
            self._levels = []
            self._ome_meta = {}

    def read_region(
        self, location: Tuple[int, int], level: int, size: Tuple[int, int]
    ) -> np.ndarray:
        """Read a region from the OME-TIFF at the specified level."""
        if self._tif is None:
            raise RuntimeError("Slide not open")

        if level < 0 or level >= len(self._levels):
            raise ValueError(f"Level {level} out of range [0, {len(self._levels) - 1}]")

        try:
            data = self._levels[level].asarray()  # type: ignore[union-attr]

            x, y = location
            w, h = size

            # Handle various array shapes: (Y, X), (Y, X, C), (C, Y, X), etc.
            if data.ndim == 2:
                region = data[y : y + h, x : x + w]
                # Convert grayscale to RGB
                region_rgb = np.stack([region, region, region], axis=-1)
            elif data.ndim == 3:
                if data.shape[2] <= 4:
                    # (Y, X, C) format
                    region = data[y : y + h, x : x + w, :3]
                    if region.shape[2] == 1:
                        region_rgb = np.concatenate([region] * 3, axis=-1)
                    else:
                        region_rgb = region[:, :, :3]
                else:
                    # (C, Y, X) format
                    region = data[:3, y : y + h, x : x + w]
                    region_rgb = np.transpose(region, (1, 2, 0))
                    if region_rgb.shape[2] == 1:
                        region_rgb = np.concatenate([region_rgb] * 3, axis=-1)
            else:
                # Higher dimensional - take first plane
                plane = data.reshape(-1, data.shape[-2], data.shape[-1])[0]
                region = plane[y : y + h, x : x + w]
                region_rgb = np.stack([region, region, region], axis=-1)

            return region_rgb.astype(np.uint8)
        except Exception as e:
            raise RuntimeError(f"Failed to read region: {e}") from e

    def get_metadata(self) -> SlideMetadata:
        """Extract metadata from the OME-TIFF."""
        if self._tif is None:
            raise RuntimeError("Slide not open")

        dims = self.level_dimensions
        width, height = dims[0] if dims else (0, 0)

        return SlideMetadata(
            width=width,
            height=height,
            level_count=len(self._levels),
            level_dimensions=dims,
            mpp_x=self._ome_meta.get("mpp_x"),
            mpp_y=self._ome_meta.get("mpp_y"),
            vendor=None,
            format_name="ome.tiff",
            channels=self._ome_meta.get("channels", 1),
            z_levels=self._ome_meta.get("z_levels", 1),
            timepoints=self._ome_meta.get("timepoints", 1),
        )

    def get_thumbnail(self, size: Tuple[int, int]) -> np.ndarray:
        """Get a thumbnail from the lowest resolution level."""
        if self._tif is None:
            raise RuntimeError("Slide not open")

        # Use lowest resolution level
        level_idx = len(self._levels) - 1 if self._levels else 0
        if not self._levels:
            raise RuntimeError("No image data found in OME-TIFF")

        data = self._levels[level_idx].asarray()  # type: ignore[union-attr]

        # Get 2D representation
        if data.ndim == 2:
            img = data
        elif data.ndim == 3:
            img = data[:, :, 0] if data.shape[2] <= 4 else data[0]
        else:
            img = data.reshape(-1, data.shape[-2], data.shape[-1])[0]

        # Resize to fit within the requested size
        from_h, from_w = img.shape[:2]
        max_w, max_h = size
        scale = min(max_w / max(from_w, 1), max_h / max(from_h, 1), 1.0)
        new_w = max(1, int(from_w * scale))
        new_h = max(1, int(from_h * scale))

        # Simple downsampling by slicing
        step_y = max(1, from_h // new_h)
        step_x = max(1, from_w // new_w)
        thumb = img[::step_y, ::step_x]

        # Convert to RGB
        thumb_rgb = np.stack([thumb, thumb, thumb], axis=-1) if thumb.ndim == 2 else thumb[:, :, :3]

        return thumb_rgb.astype(np.uint8)

    @property
    def dimensions(self) -> Tuple[int, int]:
        """Slide dimensions at level 0."""
        if self._tif is None:
            raise RuntimeError("Slide not open")
        dims = self.level_dimensions
        return dims[0] if dims else (0, 0)

    @property
    def level_count(self) -> int:
        """Number of pyramid levels."""
        if self._tif is None:
            raise RuntimeError("Slide not open")
        return len(self._levels)

    @property
    def level_dimensions(self) -> List[Tuple[int, int]]:
        """Dimensions of each pyramid level."""
        if self._tif is None:
            raise RuntimeError("Slide not open")

        dims = []
        for series in self._levels:
            shape = series.shape  # type: ignore[union-attr]
            # Shape might be (Y, X), (Y, X, C), (C, Y, X), etc.
            if len(shape) == 2:
                dims.append((shape[1], shape[0]))
            elif len(shape) == 3:
                if shape[2] <= 4:
                    dims.append((shape[1], shape[0]))
                else:
                    dims.append((shape[2], shape[1]))
            else:
                dims.append((shape[-1], shape[-2]))
        return dims

    @classmethod
    def supported_formats(cls) -> List[str]:
        """Return list of supported file extensions."""
        return ["ome.tiff", "ome.tif"]

    @classmethod
    def can_open(cls, path: str) -> int:
        """
        Return confidence score for ability to open this file.

        Checks for OME-XML in the TIFF description tag.
        Returns 85 for OME-TIFF files, 0 for others.
        Returns 0 if tifffile is not installed.
        """
        if not _HAS_TIFFFILE:
            return 0

        # Check file extension first (fast path)
        path_lower = path.lower()
        has_ome_ext = path_lower.endswith(".ome.tiff") or path_lower.endswith(".ome.tif")
        has_tif_ext = path_lower.endswith(".tif") or path_lower.endswith(".tiff")
        if not has_ome_ext and not has_tif_ext:
            return 0

        # Check for OME-XML in description
        if _is_ome_tiff(path):
            return 85

        return 0
