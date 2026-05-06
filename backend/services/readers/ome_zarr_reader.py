"""
OME-Zarr Reader

Implements ISlideReader for OME-Zarr datasets using the zarr library.
OME-Zarr (also known as NGFF) stores image pyramids as chunked arrays
in the Zarr format with OME metadata in .zattrs.

This reader:
- Uses zarr for lazy, chunked array access
- Checks for .zattrs containing "multiscales" key
- Falls back gracefully if zarr is not installed
- Supports multi-resolution pyramids

Supported formats:
- .zarr / .ome.zarr directories

Issue #41: OME-Zarr Reader
References:
- OME-NGFF spec: https://ngff.openmicroscopy.org/
- zarr-python: https://zarr.readthedocs.io/
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base import SlideMetadata, SlideReaderBase

logger = logging.getLogger(__name__)

# Try to import optional dependency
_HAS_ZARR = False
try:
    import zarr

    _HAS_ZARR = True
except ImportError:
    zarr = None  # type: ignore[assignment]


def _is_ome_zarr(path: str) -> bool:
    """
    Check if a directory is an OME-Zarr dataset.

    Looks for .zattrs file containing the "multiscales" key,
    which is the defining feature of OME-NGFF datasets.
    """
    zarr_path = Path(path)
    if not zarr_path.is_dir():
        return False

    zattrs_path = zarr_path / ".zattrs"
    if not zattrs_path.exists():
        return False

    try:
        with open(zattrs_path) as f:
            attrs = json.load(f)
        return "multiscales" in attrs
    except Exception:
        return False


class OMEZarrReader(SlideReaderBase):
    """
    Slide reader for OME-Zarr datasets using the zarr library.

    OME-Zarr stores pyramid levels as separate arrays within a Zarr group.
    This reader provides lazy access to chunks, loading only the data
    needed for each operation.

    Examples:
        >>> reader = OMEZarrReader()
        >>> reader.open("/path/to/slide.zarr")
        >>> meta = reader.get_metadata()
        >>> region = reader.read_region((0, 0), 0, (256, 256))
    """

    def __init__(self) -> None:
        self._store: Optional[object] = None
        self._path: Optional[str] = None
        self._arrays: List[Any] = []  # zarr arrays for each level
        self._multiscales_meta: Dict = {}

    def open(self, path: str) -> None:
        """Open an OME-Zarr dataset."""
        if not _HAS_ZARR:
            raise RuntimeError(
                "OMEZarrReader requires the zarr package. " "Install with: pip install zarr"
            )

        zarr_path = Path(path)
        if not zarr_path.exists():
            raise FileNotFoundError(f"Zarr dataset not found: {path}")

        if not zarr_path.is_dir():
            raise RuntimeError(f"OME-Zarr path must be a directory: {path}")

        try:
            store = zarr.open(path, mode="r")
        except Exception as e:
            raise RuntimeError(f"Cannot open OME-Zarr {path}: {e}") from e

        self._store = store

        # Parse multiscales metadata from .zattrs
        attrs = dict(store.attrs) if hasattr(store, "attrs") else {}
        multiscales = attrs.get("multiscales", [])

        if multiscales:
            self._multiscales_meta = multiscales[0]
            # Load arrays for each pyramid level
            datasets = self._multiscales_meta.get("datasets", [])
            for ds in datasets:
                ds_path = ds.get("path", "")
                if ds_path and ds_path in store:
                    self._arrays.append(store[ds_path])
                elif ds_path:
                    logger.warning(f"Dataset path '{ds_path}' not found in Zarr store")
        elif hasattr(store, "shape"):
            # No multiscales, root is an array
            self._arrays = [store]
        else:
            # No multiscales - look for numbered groups (0, 1, 2, ...)
            for key in sorted(store.keys()):
                if hasattr(store[key], "shape"):
                    self._arrays.append(store[key])

        if not self._arrays:
            msg = "No image arrays found in OME-Zarr dataset"
            raise RuntimeError(msg)

        self._path = path
        logger.info(f"OMEZarrReader opened: {zarr_path.name} " f"({len(self._arrays)} levels)")

    def close(self) -> None:
        """Close the OME-Zarr dataset."""
        self._store = None
        self._path = None
        self._arrays = []
        self._multiscales_meta = {}

    def read_region(
        self, location: Tuple[int, int], level: int, size: Tuple[int, int]
    ) -> np.ndarray:
        """Read a region from the OME-Zarr at the specified level."""
        if self._store is None:
            raise RuntimeError("Dataset not open")

        if level < 0 or level >= len(self._arrays):
            raise ValueError(f"Level {level} out of range [0, {len(self._arrays) - 1}]")

        arr = self._arrays[level]
        x, y = location
        w, h = size

        data = self._read_array_data(arr)
        region_rgb = self._extract_rgb_region(data, x, y, w, h)
        return region_rgb.astype(np.uint8)

    @staticmethod
    def _read_array_data(arr: Any) -> np.ndarray:
        """Read array data from zarr, wrapping errors."""
        try:
            return arr[...]
        except Exception as e:
            raise RuntimeError(f"Failed to read zarr array: {e}") from e

    @staticmethod
    def _extract_rgb_region(data: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Extract an RGB region from array data of various shapes."""
        shape = data.shape

        # Handle various array shapes
        if data.ndim == 2:
            region = data[y : y + h, x : x + w]
            region_rgb = np.stack([region, region, region], axis=-1)
        elif data.ndim == 3:
            if shape[0] <= 4:
                # (C, Y, X) format
                region = data[:3, y : y + h, x : x + w]
                region_rgb = np.transpose(region, (1, 2, 0))
                if region_rgb.shape[2] == 1:
                    region_rgb = np.concatenate([region_rgb] * 3, axis=-1)
            else:
                # (Y, X, C) format
                region = data[y : y + h, x : x + w, :3]
                region_rgb = region
        elif data.ndim >= 4:
            # (T, C, Y, X) or (T, Z, C, Y, X) - take first T, Z
            plane = data.reshape(-1, shape[-2], shape[-1])[0]
            region = plane[y : y + h, x : x + w]
            region_rgb = np.stack([region, region, region], axis=-1)
        else:
            msg = f"Unexpected array shape: {shape}"
            raise ValueError(msg)

        # Ensure 3 channels
        if region_rgb.shape[2] > 3:
            region_rgb = region_rgb[:, :, :3]

        return region_rgb

    def get_metadata(self) -> SlideMetadata:
        """Extract metadata from the OME-Zarr dataset."""
        if self._store is None:
            raise RuntimeError("Dataset not open")

        dims = self.level_dimensions
        width, height = dims[0] if dims else (0, 0)

        # Try to extract pixel size from coordinate transformations
        mpp_x = None
        mpp_y = None
        datasets = self._multiscales_meta.get("datasets", [])
        if datasets:
            transforms = datasets[0].get("coordinateTransformations", [])
            for t in transforms:
                if t.get("type") == "scale":
                    scale = t.get("scale", [])
                    # Scale typically ordered as (T, C, Z, Y, X) or (Y, X)
                    if len(scale) >= 2:
                        mpp_y = scale[-2]
                        mpp_x = scale[-1]

        return SlideMetadata(
            width=width,
            height=height,
            level_count=len(self._arrays),
            level_dimensions=dims,
            mpp_x=mpp_x,
            mpp_y=mpp_y,
            vendor=None,
            format_name="ome.zarr",
        )

    def get_thumbnail(self, size: Tuple[int, int]) -> np.ndarray:
        """Get a thumbnail from the lowest resolution level."""
        if self._store is None:
            raise RuntimeError("Dataset not open")

        if not self._arrays:
            raise RuntimeError("No image data found in OME-Zarr")

        # Use lowest resolution level
        arr = self._arrays[-1]
        data = arr[...]

        # Get 2D representation
        if data.ndim == 2:
            img = data
        elif data.ndim == 3:
            img = data[0] if data.shape[0] <= 4 else data[:, :, 0]
        else:
            img = data.reshape(-1, data.shape[-2], data.shape[-1])[0]

        # Resize to fit within the requested size
        from_h, from_w = img.shape[:2]
        max_w, max_h = size
        scale = min(max_w / max(from_w, 1), max_h / max(from_h, 1), 1.0)
        new_h = max(1, int(from_h * scale))
        new_w = max(1, int(from_w * scale))

        step_y = max(1, from_h // new_h)
        step_x = max(1, from_w // new_w)
        thumb = img[::step_y, ::step_x]

        # Convert to RGB
        thumb_rgb = np.stack([thumb, thumb, thumb], axis=-1) if thumb.ndim == 2 else thumb[:, :, :3]

        return thumb_rgb.astype(np.uint8)

    @property
    def dimensions(self) -> Tuple[int, int]:
        """Dataset dimensions at level 0."""
        if self._store is None:
            raise RuntimeError("Dataset not open")
        dims = self.level_dimensions
        return dims[0] if dims else (0, 0)

    @property
    def level_count(self) -> int:
        """Number of pyramid levels."""
        if self._store is None:
            raise RuntimeError("Dataset not open")
        return len(self._arrays)

    @property
    def level_dimensions(self) -> List[Tuple[int, int]]:
        """Dimensions of each pyramid level."""
        if self._store is None:
            raise RuntimeError("Dataset not open")

        dims = []
        for arr in self._arrays:
            shape = arr.shape
            if len(shape) == 2:
                dims.append((shape[1], shape[0]))
            elif len(shape) == 3 and shape[0] <= 4:
                dims.append((shape[2], shape[1]))
            elif len(shape) == 3:
                dims.append((shape[1], shape[0]))
            else:
                dims.append((shape[-1], shape[-2]))
        return dims

    @classmethod
    def supported_formats(cls) -> List[str]:
        """Return list of supported format identifiers."""
        return ["zarr", "ome.zarr"]

    @classmethod
    def can_open(cls, path: str) -> int:
        """
        Return confidence score for ability to open this file.

        Checks for .zarr directory with .zattrs containing "multiscales".
        Returns 85 for valid OME-Zarr datasets, 0 otherwise.
        Returns 0 if zarr is not installed.
        """
        if not _HAS_ZARR:
            return 0

        if _is_ome_zarr(path):
            return 85

        # Check if it looks like a zarr directory by extension
        path_lower = path.lower()
        has_zarr_ext = path_lower.endswith(".zarr") or path_lower.endswith(".ome.zarr")
        if has_zarr_ext and Path(path).is_dir():
            return 40

        return 0
