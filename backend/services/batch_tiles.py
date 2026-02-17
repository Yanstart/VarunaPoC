"""
Batch Tile Extraction Service

Extract multiple tiles from a slide in a single request, returned as a ZIP archive.

Features:
- Batch extraction of arbitrary rectangular regions
- ZIP packaging with metadata
- Mock mode when OpenSlide is unavailable
- Configurable output format (JPEG/PNG) and quality

Reference: Issue #10
"""

import io
import logging
import time
import zipfile
from dataclasses import dataclass
from typing import List, Tuple

logger = logging.getLogger(__name__)

try:
    import openslide
    from PIL import Image

    OPENSLIDE_AVAILABLE = True
except ImportError:
    OPENSLIDE_AVAILABLE = False
    logger.warning("OpenSlide not available; batch tile extraction will use mock mode")


@dataclass
class TileRegion:
    """Defines a rectangular region to extract from a slide."""

    x: int
    y: int
    level: int = 0
    w: int = 256
    h: int = 256


@dataclass
class BatchResult:
    """Metadata about a completed batch extraction."""

    tile_count: int
    total_size_bytes: int
    processing_time_ms: float
    format: str = "zip"


class BatchTileService:
    """Extract multiple tiles from a slide in a single request."""

    MAX_REGIONS = 10000

    def extract_batch(
        self,
        slide_path: str,
        regions: List[TileRegion],
        img_format: str = "jpeg",
        quality: int = 85,
    ) -> Tuple[bytes, BatchResult]:
        """
        Extract tiles and return as ZIP archive.

        Args:
            slide_path: Absolute path to the slide file.
            regions: List of TileRegion defining areas to extract.
            img_format: Image format, "jpeg" or "png".
            quality: JPEG quality (1-100). Ignored for PNG.

        Returns:
            Tuple of (ZIP bytes, BatchResult metadata).

        Raises:
            ValueError: If regions exceed MAX_REGIONS.
        """
        if len(regions) > self.MAX_REGIONS:
            raise ValueError(
                f"Too many regions: {len(regions)} exceeds maximum {self.MAX_REGIONS}"
            )

        start = time.time()

        if OPENSLIDE_AVAILABLE:
            zip_bytes = self._extract_real(slide_path, regions, img_format, quality)
        else:
            zip_bytes = self._extract_mock(regions, img_format, quality)

        elapsed_ms = (time.time() - start) * 1000

        result = BatchResult(
            tile_count=len(regions),
            total_size_bytes=len(zip_bytes),
            processing_time_ms=round(elapsed_ms, 2),
            format="zip",
        )

        return zip_bytes, result

    def _extract_real(
        self,
        slide_path: str,
        regions: List[TileRegion],
        img_format: str,
        quality: int,
    ) -> bytes:
        """Extract tiles from a real slide using OpenSlide."""
        slide = openslide.OpenSlide(slide_path)
        try:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, region in enumerate(regions):
                    tile_img = slide.read_region(
                        location=(region.x, region.y),
                        level=region.level,
                        size=(region.w, region.h),
                    )
                    # OpenSlide returns RGBA; convert to RGB for JPEG
                    rgb_img = tile_img.convert("RGB")

                    tile_buf = io.BytesIO()
                    ext = "jpg" if img_format == "jpeg" else "png"
                    if img_format == "jpeg":
                        rgb_img.save(tile_buf, format="JPEG", quality=quality, optimize=True)
                    else:
                        rgb_img.save(tile_buf, format="PNG")
                    tile_buf.seek(0)

                    filename = f"tile_{i:05d}_x{region.x}_y{region.y}_l{region.level}.{ext}"
                    zf.writestr(filename, tile_buf.getvalue())

            buf.seek(0)
            return buf.getvalue()
        finally:
            slide.close()

    def _extract_mock(
        self,
        regions: List[TileRegion],
        img_format: str,
        quality: int,
    ) -> bytes:
        """Generate mock tiles (solid-color images) when OpenSlide is unavailable."""
        from PIL import Image as PILImage

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, region in enumerate(regions):
                # Deterministic color based on region coordinates
                r = (region.x * 17 + region.y * 31) % 256
                g = (region.x * 53 + region.y * 7) % 256
                b = (region.x * 97 + region.y * 13) % 256
                img = PILImage.new("RGB", (region.w, region.h), (r, g, b))

                tile_buf = io.BytesIO()
                ext = "jpg" if img_format == "jpeg" else "png"
                if img_format == "jpeg":
                    img.save(tile_buf, format="JPEG", quality=quality)
                else:
                    img.save(tile_buf, format="PNG")
                tile_buf.seek(0)

                filename = f"tile_{i:05d}_x{region.x}_y{region.y}_l{region.level}.{ext}"
                zf.writestr(filename, tile_buf.getvalue())

        buf.seek(0)
        return buf.getvalue()
