"""
Tile Server Tests

Comprehensive unit tests for backend/services/tile_server.py.

Tests cover:
- Valid tile extraction (mocked OpenSlide)
- Out-of-bounds coordinates
- Invalid pyramid level
- Slide cache behavior (open, evict, reuse)
- DZI metadata generation
- Error handling (missing file, OpenSlide errors)
- Edge tile handling (partial tiles at boundaries)
- RGBA to RGB conversion
- JPEG output encoding

All OpenSlide interactions are mocked since no real slide files are
available in the test environment.
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from services.tile_server import TileServer, tile_server

# =========================================================================
# Helpers
# =========================================================================


def _make_mock_slide(
    dimensions=(100000, 80000),
    level_count=3,
    level_dimensions=None,
    level_downsamples=None,
):
    """Create a mock OpenSlide object with standard properties."""
    slide = MagicMock()
    slide.dimensions = dimensions
    slide.level_count = level_count

    if level_dimensions is None:
        level_dimensions = [
            (100000, 80000),
            (50000, 40000),
            (25000, 20000),
        ]
    slide.level_dimensions = level_dimensions

    if level_downsamples is None:
        level_downsamples = [1.0, 2.0, 4.0]
    slide.level_downsamples = level_downsamples

    # read_region returns a mock RGBA PIL Image
    rgba_image = Image.new("RGBA", (256, 256), (200, 100, 50, 255))
    slide.read_region.return_value = rgba_image

    return slide


# =========================================================================
# TileServer initialization
# =========================================================================


class TestTileServerInit:
    """Tests for TileServer constructor and initial state."""

    def test_initial_cache_empty(self):
        """TileServer should start with empty cache."""
        ts = TileServer()
        assert ts._slide_cache == {}
        assert ts._max_cache_size == 5

    def test_global_singleton_exists(self):
        """The module-level tile_server singleton should exist."""
        assert tile_server is not None
        assert isinstance(tile_server, TileServer)


# =========================================================================
# get_slide tests
# =========================================================================


class TestGetSlide:
    """Tests for the get_slide method (cache + open)."""

    @patch("services.tile_server.openslide.OpenSlide")
    def test_open_new_slide(self, mock_os_cls, tmp_path):
        """Opening a new slide should call OpenSlide and cache it."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        mock_slide = _make_mock_slide()
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        result = ts.get_slide(str(slide_file))

        assert result is mock_slide
        assert str(slide_file) in ts._slide_cache
        mock_os_cls.assert_called_once_with(str(slide_file))

    @patch("services.tile_server.openslide.OpenSlide")
    def test_cache_hit(self, mock_os_cls, tmp_path):
        """Requesting same slide twice should use cache (no second OpenSlide call)."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        mock_slide = _make_mock_slide()
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        first = ts.get_slide(str(slide_file))
        second = ts.get_slide(str(slide_file))

        assert first is second
        # OpenSlide should only be called once
        mock_os_cls.assert_called_once()

    def test_file_not_found(self):
        """Opening a non-existent slide should raise FileNotFoundError."""
        ts = TileServer()
        with pytest.raises(FileNotFoundError, match="Slide not found"):
            ts.get_slide("/nonexistent/path/slide.svs")

    @patch("services.tile_server.openslide.OpenSlide")
    def test_cache_eviction(self, mock_os_cls, tmp_path):
        """When cache is full, oldest slide should be evicted."""
        ts = TileServer()
        ts._max_cache_size = 2

        slides = []
        mocks = []
        for i in range(3):
            p = tmp_path / f"slide{i}.svs"
            p.write_bytes(b"\x00" * 10)
            slides.append(str(p))
            m = _make_mock_slide()
            mocks.append(m)

        mock_os_cls.side_effect = mocks

        ts.get_slide(slides[0])
        ts.get_slide(slides[1])
        assert len(ts._slide_cache) == 2

        # This should evict slide0
        ts.get_slide(slides[2])
        assert len(ts._slide_cache) == 2
        assert slides[0] not in ts._slide_cache
        assert slides[1] in ts._slide_cache
        assert slides[2] in ts._slide_cache
        # The evicted slide should have been closed
        mocks[0].close.assert_called_once()


# =========================================================================
# get_tile tests
# =========================================================================


class TestGetTile:
    """Tests for tile extraction."""

    @patch("services.tile_server.openslide.OpenSlide")
    def test_valid_tile(self, mock_os_cls, tmp_path):
        """Extracting a valid tile should return JPEG bytes."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        mock_slide = _make_mock_slide()
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        result = ts.get_tile(str(slide_file), level=0, col=0, row=0)

        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        # Should be valid JPEG
        assert result[:2] == b"\xff\xd8"

    @patch("services.tile_server.openslide.OpenSlide")
    def test_tile_is_rgb_jpeg(self, mock_os_cls, tmp_path):
        """Tile output should be RGB JPEG (not RGBA)."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        mock_slide = _make_mock_slide()
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        result = ts.get_tile(str(slide_file), level=0, col=0, row=0)

        # Decode the JPEG and verify it is RGB
        img = Image.open(io.BytesIO(result))
        assert img.mode == "RGB"
        assert img.size == (256, 256)

    @patch("services.tile_server.openslide.OpenSlide")
    def test_invalid_level_negative(self, mock_os_cls, tmp_path):
        """Negative level should return None."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)
        mock_os_cls.return_value = _make_mock_slide()

        ts = TileServer()
        result = ts.get_tile(str(slide_file), level=-1, col=0, row=0)
        assert result is None

    @patch("services.tile_server.openslide.OpenSlide")
    def test_invalid_level_too_high(self, mock_os_cls, tmp_path):
        """Level beyond level_count should return None."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)
        mock_os_cls.return_value = _make_mock_slide(level_count=3)

        ts = TileServer()
        result = ts.get_tile(str(slide_file), level=5, col=0, row=0)
        assert result is None

    @patch("services.tile_server.openslide.OpenSlide")
    def test_out_of_bounds_col(self, mock_os_cls, tmp_path):
        """Column beyond slide width should return None."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)
        mock_os_cls.return_value = _make_mock_slide(
            level_dimensions=[(1000, 1000), (500, 500)],
            level_count=2,
            level_downsamples=[1.0, 2.0],
        )

        ts = TileServer()
        # col=4 means x=1024 which is >= width=1000 at level 0
        result = ts.get_tile(str(slide_file), level=0, col=4, row=0)
        assert result is None

    @patch("services.tile_server.openslide.OpenSlide")
    def test_out_of_bounds_row(self, mock_os_cls, tmp_path):
        """Row beyond slide height should return None."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)
        mock_os_cls.return_value = _make_mock_slide(
            level_dimensions=[(1000, 500), (500, 250)],
            level_count=2,
            level_downsamples=[1.0, 2.0],
        )

        ts = TileServer()
        # row=2 means y=512 which is >= height=500 at level 0
        result = ts.get_tile(str(slide_file), level=0, col=0, row=2)
        assert result is None

    @patch("services.tile_server.openslide.OpenSlide")
    def test_edge_tile_padded(self, mock_os_cls, tmp_path):
        """Edge tile (partial) should be padded to full tile_size."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        # Level 0 is 300x300 -- col=1, row=1 means x=256,y=256
        # actual_width = min(256, 300-256) = 44, actual_height = 44
        mock_slide = _make_mock_slide(
            dimensions=(300, 300),
            level_count=1,
            level_dimensions=[(300, 300)],
            level_downsamples=[1.0],
        )
        # Return a small RGBA image matching the partial size
        partial = Image.new("RGBA", (44, 44), (100, 100, 100, 255))
        mock_slide.read_region.return_value = partial
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        result = ts.get_tile(str(slide_file), level=0, col=1, row=1)

        assert result is not None
        img = Image.open(io.BytesIO(result))
        assert img.size == (256, 256)  # Padded to full tile

    @patch("services.tile_server.openslide.OpenSlide")
    def test_coordinate_conversion(self, mock_os_cls, tmp_path):
        """Tile coordinates should be converted to level-0 coordinates for OpenSlide."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        mock_slide = _make_mock_slide(
            level_dimensions=[(10000, 10000), (5000, 5000)],
            level_count=2,
            level_downsamples=[1.0, 2.0],
        )
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        ts.get_tile(str(slide_file), level=1, col=2, row=3, tile_size=256)

        # At level 1, downsample=2.0
        # x_tile = 2*256 = 512, y_tile = 3*256 = 768
        # x_level0 = int(512 * 2.0) = 1024, y_level0 = int(768 * 2.0) = 1536
        mock_slide.read_region.assert_called_once()
        call_args = mock_slide.read_region.call_args
        # read_region may be called with positional or keyword args
        if "location" in call_args.kwargs:
            location = call_args.kwargs["location"]
        else:
            location = call_args.args[0]
        assert location == (1024, 1536)

    @patch("services.tile_server.openslide.OpenSlide")
    def test_custom_tile_size(self, mock_os_cls, tmp_path):
        """Custom tile_size should be respected."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        mock_slide = _make_mock_slide()
        tile_img = Image.new("RGBA", (512, 512), (50, 50, 50, 255))
        mock_slide.read_region.return_value = tile_img
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        result = ts.get_tile(str(slide_file), level=0, col=0, row=0, tile_size=512)

        assert result is not None
        img = Image.open(io.BytesIO(result))
        assert img.size == (512, 512)

    def test_tile_file_not_found(self):
        """get_tile for non-existent file should return None (caught)."""
        ts = TileServer()
        result = ts.get_tile("/nonexistent/slide.svs", level=0, col=0, row=0)
        assert result is None

    @patch("services.tile_server.openslide.OpenSlide")
    def test_tile_openslide_error(self, mock_os_cls, tmp_path):
        """OpenSlide error during read_region should return None."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        import openslide

        mock_slide = _make_mock_slide()
        mock_slide.read_region.side_effect = openslide.OpenSlideError("read failed")
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        result = ts.get_tile(str(slide_file), level=0, col=0, row=0)
        assert result is None

    @patch("services.tile_server.openslide.OpenSlide")
    def test_tile_unexpected_error(self, mock_os_cls, tmp_path):
        """Unexpected error during tile extraction should return None."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        mock_slide = _make_mock_slide()
        mock_slide.read_region.side_effect = RuntimeError("unexpected")
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        result = ts.get_tile(str(slide_file), level=0, col=0, row=0)
        assert result is None


# =========================================================================
# get_dzi_metadata tests
# =========================================================================


class TestGetDZIMetadata:
    """Tests for DZI metadata generation."""

    @patch("services.tile_server.openslide.OpenSlide")
    def test_dzi_metadata_structure(self, mock_os_cls, tmp_path):
        """DZI metadata should contain all required fields."""
        slide_file = tmp_path / "slide.svs"
        slide_file.write_bytes(b"\x00" * 10)

        mock_slide = _make_mock_slide(
            dimensions=(100000, 80000),
            level_count=3,
            level_dimensions=[(100000, 80000), (50000, 40000), (25000, 20000)],
            level_downsamples=[1.0, 2.0, 4.0],
        )
        mock_os_cls.return_value = mock_slide

        ts = TileServer()
        meta = ts.get_dzi_metadata(str(slide_file))

        assert meta["width"] == 100000
        assert meta["height"] == 80000
        assert meta["tile_size"] == 256
        assert meta["overlap"] == 0
        assert meta["format"] == "jpeg"
        assert meta["levels"] == 3
        assert meta["level_dimensions"] == [(100000, 80000), (50000, 40000), (25000, 20000)]
        assert meta["level_downsamples"] == [1.0, 2.0, 4.0]

    def test_dzi_file_not_found(self):
        """DZI metadata for non-existent file should raise FileNotFoundError."""
        ts = TileServer()
        with pytest.raises(FileNotFoundError):
            ts.get_dzi_metadata("/nonexistent/slide.svs")


# =========================================================================
# close_all and cleanup tests
# =========================================================================


class TestCloseAll:
    """Tests for cache cleanup."""

    @patch("services.tile_server.openslide.OpenSlide")
    def test_close_all(self, mock_os_cls, tmp_path):
        """close_all should close all cached slides and clear cache."""
        ts = TileServer()

        slides = []
        mocks = []
        for i in range(3):
            p = tmp_path / f"slide{i}.svs"
            p.write_bytes(b"\x00" * 10)
            slides.append(str(p))
            m = _make_mock_slide()
            mocks.append(m)

        mock_os_cls.side_effect = mocks

        for s in slides:
            ts.get_slide(s)

        assert len(ts._slide_cache) == 3

        ts.close_all()

        assert len(ts._slide_cache) == 0
        for m in mocks:
            m.close.assert_called_once()

    def test_close_all_on_empty_cache(self):
        """close_all on empty cache should not raise."""
        ts = TileServer()
        ts.close_all()  # Should not raise
        assert ts._slide_cache == {}
