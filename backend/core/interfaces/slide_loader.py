"""
Slide Loader Interface

PURPOSE: Abstract slide loading across different formats.
VarunaPoC currently uses OpenSlide for 12 formats, but may need:
- Custom loaders for proprietary formats
- Optimized loaders for specific vendors
- GPU-accelerated loaders (CUDA)
- Format converters (e.g., JP2 → PNG on-the-fly)

Pattern: Strategy Pattern + Factory Pattern
"""

from typing import Protocol, Optional, Dict, List, Tuple
from pathlib import Path
from PIL import Image
import numpy as np


class SlideLoader(Protocol):
    """
    Protocol for slide format loaders.

    Default Implementation: OpenSlideLoader (existing slide_loader.py)
    Alternative Implementations:
    - BioformatsLoader (support more formats via Bio-Formats)
    - VipsLoader (libvips - faster than OpenSlide for some formats)
    - CustomMRXSLoader (optimized 3DHistech reader)
    - DicomWsiLoader (DICOM-specific loader)

    Why Protocol?
    - Allows swapping loaders without code changes
    - Easy to A/B test performance (OpenSlide vs VIPS)
    - Supports custom proprietary formats
    """

    def can_open(self, file_path: Path) -> bool:
        """
        Check if this loader can open the given file.

        Args:
            file_path: Path to slide file

        Returns:
            True if loader supports this format

        Examples:
            >>> loader = OpenSlideLoader()
            >>> loader.can_open(Path("sample.mrxs"))  # True
            >>> loader.can_open(Path("image.png"))    # False

        Notes:
            - SHOULD use OpenSlide.detect_format() or similar
            - MUST NOT raise exceptions (return False instead)
        """
        ...

    def get_metadata(self, file_path: Path) -> Dict:
        """
        Extract slide metadata.

        Args:
            file_path: Path to slide file

        Returns:
            Dict with keys:
            - dimensions: Tuple[int, int] (width, height at level 0)
            - level_count: int
            - level_dimensions: List[Tuple[int, int]]
            - level_downsamples: List[float]
            - vendor: str (e.g., "3DHISTECH", "Roche")
            - format: str (e.g., "mirax", "ventana")
            - properties: Dict (vendor-specific properties)

        Examples:
            >>> metadata = loader.get_metadata(Path("sample.mrxs"))
            >>> print(metadata["dimensions"])  # (100000, 80000)
            >>> print(metadata["vendor"])  # "3DHISTECH"

        Notes:
            - MUST open slide temporarily (close after)
            - SHOULD cache metadata (avoid repeated opens)
            - Properties may include:
              - openslide.mpp-x, openslide.mpp-y (microns per pixel)
              - openslide.objective-power (magnification)
              - tiff.DateTime (scan timestamp)
        """
        ...

    def read_region(
        self,
        file_path: Path,
        location: Tuple[int, int],
        level: int,
        size: Tuple[int, int]
    ) -> Image.Image:
        """
        Read rectangular region from slide.

        Args:
            file_path: Path to slide file
            location: (x, y) coordinates at LEVEL 0 (OpenSlide convention)
            level: Pyramid level to read from (0 = highest resolution)
            size: (width, height) in pixels at requested level

        Returns:
            PIL Image (RGBA or RGB)

        Examples:
            >>> # Read 256x256 tile at level 2, position (1000, 2000)
            >>> tile = loader.read_region(
            ...     file_path=Path("sample.mrxs"),
            ...     location=(1000, 2000),
            ...     level=2,
            ...     size=(256, 256)
            ... )

        Notes:
            - OpenSlide returns RGBA (must convert to RGB for JPEG)
            - Location coordinates are ALWAYS at level 0 (highest res)
            - Size is at the requested level
            - MUST handle out-of-bounds gracefully (return black/white)
        """
        ...

    def get_thumbnail(
        self,
        file_path: Path,
        max_size: Tuple[int, int] = (2000, 2000)
    ) -> Image.Image:
        """
        Get slide thumbnail (overview image).

        Args:
            file_path: Path to slide file
            max_size: Maximum dimensions (preserves aspect ratio)

        Returns:
            PIL Image (RGB)

        Examples:
            >>> thumbnail = loader.get_thumbnail(
            ...     file_path=Path("sample.mrxs"),
            ...     max_size=(1000, 1000)
            ... )

        Notes:
            - OpenSlide.get_thumbnail() handles this automatically
            - Chooses optimal pyramid level for performance
            - MUST preserve aspect ratio
        """
        ...

    def get_associated_images(self, file_path: Path) -> Dict[str, Image.Image]:
        """
        Get associated images (label, macro, thumbnail).

        Args:
            file_path: Path to slide file

        Returns:
            Dict mapping image type → PIL Image
            Common keys: "label", "macro", "thumbnail"

        Examples:
            >>> images = loader.get_associated_images(Path("sample.mrxs"))
            >>> if "label" in images:
            ...     label = images["label"]  # Barcode/label image

        Notes:
            - Not all formats have associated images
            - 3DHistech MRXS: typically has "label" and "macro"
            - Ventana BIF: may have "thumbnail" and "macro"
            - DICOM WSI: associated images in separate frames
        """
        ...

    def read_region_as_array(
        self,
        file_path: Path,
        location: Tuple[int, int],
        level: int,
        size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Read region as NumPy array (for ML/image processing).

        Args:
            file_path: Path to slide file
            location: (x, y) at level 0
            level: Pyramid level
            size: (width, height) at level

        Returns:
            NumPy array (shape: [height, width, channels])
            dtype: uint8, channels: 3 (RGB) or 4 (RGBA)

        Use Cases:
            - ML inference (PyTorch, TensorFlow expect NumPy)
            - Image processing (OpenCV, scikit-image)
            - Batch processing (avoid PIL overhead)

        Examples:
            >>> tile = loader.read_region_as_array(
            ...     file_path=Path("sample.mrxs"),
            ...     location=(1000, 2000),
            ...     level=2,
            ...     size=(256, 256)
            ... )
            >>> print(tile.shape)  # (256, 256, 3)
            >>> print(tile.dtype)  # uint8
        """
        ...

    def close(self, file_path: Path) -> None:
        """
        Close slide (release resources).

        Args:
            file_path: Path to slide to close

        Notes:
            - Loaders MAY cache open slides (tile_server.py does this)
            - close() releases file handles, memory
            - Idempotent (multiple calls OK)

        Examples:
            >>> loader.close(Path("sample.mrxs"))
        """
        ...

    def get_format_info(self) -> Dict:
        """
        Get information about supported formats.

        Returns:
            Dict with keys:
            - name: str (e.g., "OpenSlide")
            - version: str (e.g., "4.0.0")
            - supported_formats: List[str] (e.g., ["mrxs", "bif", "svs"])
            - capabilities: List[str] (e.g., ["pyramidal", "associated_images"])

        Examples:
            >>> info = loader.get_format_info()
            >>> print(info["supported_formats"])
            ['mrxs', 'bif', 'svs', 'ndpi', 'scn', ...]
        """
        ...


class OptimizedSlideLoader(SlideLoader, Protocol):
    """
    Extension for loaders with performance optimizations.

    Use Cases:
    - GPU-accelerated decoding (CUDA)
    - Parallel tile extraction (multi-threading)
    - Batch processing (extract multiple tiles at once)
    - Hardware acceleration (Intel IPP, ARM NEON)
    """

    def read_regions_batch(
        self,
        file_path: Path,
        regions: List[Tuple[Tuple[int, int], int, Tuple[int, int]]]
    ) -> List[Image.Image]:
        """
        Read multiple regions in a single call (optimized).

        Args:
            file_path: Path to slide
            regions: List of (location, level, size) tuples

        Returns:
            List of PIL Images

        Benefits:
            - Amortize file I/O overhead
            - Enable parallel decoding
            - Batch GPU transfers

        Examples:
            >>> regions = [
            ...     ((0, 0), 0, (256, 256)),
            ...     ((256, 0), 0, (256, 256)),
            ...     ((512, 0), 0, (256, 256))
            ... ]
            >>> tiles = loader.read_regions_batch(Path("sample.mrxs"), regions)
        """
        ...

    def prefetch_regions(
        self,
        file_path: Path,
        regions: List[Tuple[Tuple[int, int], int, Tuple[int, int]]]
    ) -> None:
        """
        Prefetch regions into cache (non-blocking).

        Args:
            file_path: Path to slide
            regions: List of (location, level, size) tuples

        Use Cases:
            - Viewer panning (prefetch adjacent tiles)
            - ML inference (prefetch next batch)
            - Predictive loading (based on viewport)

        Examples:
            >>> # Prefetch tiles around current viewport
            >>> loader.prefetch_regions(Path("sample.mrxs"), next_tiles)
            >>> # Continue without blocking, tiles will be cached
        """
        ...
