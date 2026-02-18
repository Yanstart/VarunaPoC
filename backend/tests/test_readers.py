"""
Tests for the Reader Architecture

Comprehensive tests covering:
1. ISlideReader ABC cannot be instantiated directly
2. OpenSlideReader.can_open() scores correctly
3. OpenSlideReader.open/read_region/close with mocked openslide
4. BioFormatsReader returns 0 for can_open when no JRE
5. ReaderSelector picks highest-scoring reader
6. ReaderSelector fallback when first reader fails
7. NoCompatibleReaderError when no reader works
8. OMETIFFReader.can_open() with mocked tifffile
9. OMEZarrReader.can_open() with mocked zarr
10. Context manager protocol works
11. SlideMetadata dataclass fields

External dependencies (openslide, tifffile, zarr) are mocked since they
may not be available in all test environments.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from services.readers.base import ISlideReader, SlideMetadata
from services.readers.bioformats_reader import BioFormatsReader
from services.readers.ome_tiff_reader import OMETIFFReader, _parse_ome_xml
from services.readers.ome_zarr_reader import OMEZarrReader, _is_ome_zarr
from services.readers.openslide_reader import OpenSlideReader
from services.readers.selector import NoCompatibleReaderError, ReaderSelector, default_selector

# ============================================================================
# Helper: create mock reader classes for selector tests
# ============================================================================


def _make_mock_reader(name, score, open_succeeds=True):
    """Create a mock ISlideReader subclass with configurable score and open behavior."""

    class _MockReader(ISlideReader):
        _name = name
        _score = score
        _open_succeeds = open_succeeds

        def open(self, path):  # noqa: ARG002
            if not self._open_succeeds:
                msg = f"{self._name} cannot open"
                raise RuntimeError(msg)

        def close(self):
            pass

        def read_region(self, location, level, size):  # noqa: ARG002
            return np.zeros((10, 10, 3), dtype=np.uint8)

        def get_metadata(self):
            return SlideMetadata(
                width=100, height=100, level_count=1, level_dimensions=[(100, 100)]
            )

        def get_thumbnail(self, size):  # noqa: ARG002
            return np.zeros((10, 10, 3), dtype=np.uint8)

        @property
        def dimensions(self):
            return (100, 100)

        @property
        def level_count(self):
            return 1

        @property
        def level_dimensions(self):
            return [(100, 100)]

        @classmethod
        def supported_formats(cls):
            return ["test"]

        @classmethod
        def can_open(cls, path):  # noqa: ARG003
            return cls._score

    _MockReader.__name__ = name
    _MockReader.__qualname__ = name
    return _MockReader


# ============================================================================
# 1. ISlideReader ABC Tests
# ============================================================================


class TestISlideReaderABC:
    """Test that ISlideReader ABC cannot be instantiated directly."""

    def test_cannot_instantiate_abc(self):
        """ISlideReader is abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="abstract method"):
            ISlideReader()

    def test_must_implement_all_abstract_methods(self):
        """A partial implementation should also fail to instantiate."""

        class PartialReader(ISlideReader):
            def open(self, path):
                pass

            def close(self):
                pass

        with pytest.raises(TypeError):
            PartialReader()

    def test_concrete_subclass_can_be_instantiated(self):
        """A complete concrete implementation should be instantiable."""

        class ConcreteReader(ISlideReader):
            def open(self, path):
                pass

            def close(self):
                pass

            def read_region(self, location, level, size):  # noqa: ARG002
                return np.zeros((10, 10, 3), dtype=np.uint8)

            def get_metadata(self):
                return SlideMetadata(
                    width=100, height=100, level_count=1, level_dimensions=[(100, 100)]
                )

            def get_thumbnail(self, size):  # noqa: ARG002
                return np.zeros((10, 10, 3), dtype=np.uint8)

            @property
            def dimensions(self):
                return (100, 100)

            @property
            def level_count(self):
                return 1

            @property
            def level_dimensions(self):
                return [(100, 100)]

            @classmethod
            def supported_formats(cls):
                return ["test"]

            @classmethod
            def can_open(cls, path):  # noqa: ARG003
                return 50

        reader = ConcreteReader()
        assert reader is not None
        assert reader.can_open("test.test") == 50


# ============================================================================
# 2. OpenSlideReader.can_open() Tests
# ============================================================================


class TestOpenSlideReaderCanOpen:
    """Test OpenSlideReader.can_open() scoring logic."""

    def test_svs_scores_90(self):
        assert OpenSlideReader.can_open("slide.svs") == 90

    def test_ndpi_scores_90(self):
        assert OpenSlideReader.can_open("slide.ndpi") == 90

    def test_mrxs_scores_90(self):
        assert OpenSlideReader.can_open("slide.mrxs") == 90

    def test_bif_scores_90(self):
        assert OpenSlideReader.can_open("slide.bif") == 90

    def test_scn_scores_90(self):
        assert OpenSlideReader.can_open("slide.scn") == 90

    def test_tiff_scores_80(self):
        assert OpenSlideReader.can_open("slide.tiff") == 80

    def test_tif_scores_80(self):
        assert OpenSlideReader.can_open("slide.tif") == 80

    def test_unknown_scores_0(self):
        assert OpenSlideReader.can_open("slide.xyz") == 0

    def test_png_scores_0(self):
        assert OpenSlideReader.can_open("image.png") == 0

    def test_case_insensitive(self):
        assert OpenSlideReader.can_open("slide.SVS") == 90
        assert OpenSlideReader.can_open("slide.Ndpi") == 90

    def test_supported_formats_list(self):
        formats = OpenSlideReader.supported_formats()
        assert "svs" in formats
        assert "ndpi" in formats
        assert "mrxs" in formats
        assert "bif" in formats
        assert "scn" in formats
        assert "tif" in formats
        assert "tiff" in formats


# ============================================================================
# 3. OpenSlideReader with mocked openslide
# ============================================================================


class TestOpenSlideReaderMocked:
    """Test OpenSlideReader open/read_region/close with mocked openslide."""

    def _create_mock_openslide(self):
        """Create a mock openslide module and OpenSlide object."""
        mock_slide = MagicMock()
        mock_slide.dimensions = (100000, 80000)
        mock_slide.level_count = 3
        mock_slide.level_dimensions = [(100000, 80000), (50000, 40000), (25000, 20000)]
        mock_slide.level_downsamples = [1.0, 2.0, 4.0]
        mock_slide.properties = {
            "openslide.vendor": "aperio",
            "openslide.mpp-x": "0.25",
            "openslide.mpp-y": "0.25",
            "openslide.objective-power": "40",
        }

        # read_region returns a PIL-like object
        mock_region = MagicMock()
        mock_region.convert.return_value = MagicMock()
        mock_rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        mock_region.convert.return_value.__array_interface__ = mock_rgb.__array_interface__
        mock_slide.read_region.return_value = mock_region

        # get_thumbnail returns a PIL-like object
        mock_thumb = MagicMock()
        mock_thumb_rgb = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_thumb.convert.return_value.__array_interface__ = mock_thumb_rgb.__array_interface__
        mock_slide.get_thumbnail.return_value = mock_thumb

        return mock_slide

    @patch("services.readers.openslide_reader.openslide", create=True)
    def test_open_and_close(self, patched_openslide):  # noqa: ARG002
        """Test opening and closing a slide."""
        mock_slide = self._create_mock_openslide()

        mock_openslide = MagicMock()
        mock_openslide.OpenSlide.return_value = mock_slide

        with patch.dict("sys.modules", {"openslide": mock_openslide}):
            reader = OpenSlideReader()

            with tempfile.NamedTemporaryFile(suffix=".svs") as tmp:
                reader.open(tmp.name)
                assert reader._slide is not None
                reader.close()
                assert reader._slide is None

    @patch("services.readers.openslide_reader.openslide", create=True)
    def test_read_region(self, patched_openslide):  # noqa: ARG002
        """Test reading a region returns numpy array."""
        mock_slide = self._create_mock_openslide()

        from PIL import Image

        test_image = Image.new("RGBA", (256, 256), (128, 64, 32, 255))
        mock_slide.read_region.return_value = test_image

        mock_openslide = MagicMock()
        mock_openslide.OpenSlide.return_value = mock_slide

        with patch.dict("sys.modules", {"openslide": mock_openslide}):
            reader = OpenSlideReader()
            with tempfile.NamedTemporaryFile(suffix=".svs") as tmp:
                reader.open(tmp.name)
                region = reader.read_region((0, 0), 0, (256, 256))
                assert isinstance(region, np.ndarray)
                assert region.shape == (256, 256, 3)
                assert region.dtype == np.uint8
                reader.close()

    def test_read_region_without_open_raises(self):
        """Reading from a closed reader should raise RuntimeError."""
        reader = OpenSlideReader()
        with pytest.raises(RuntimeError, match="not open"):
            reader.read_region((0, 0), 0, (256, 256))

    def test_dimensions_without_open_raises(self):
        """Accessing dimensions on closed reader should raise."""
        reader = OpenSlideReader()
        with pytest.raises(RuntimeError, match="not open"):
            _ = reader.dimensions

    def test_open_nonexistent_file_raises(self):
        """Opening a nonexistent file should raise FileNotFoundError."""
        reader = OpenSlideReader()
        with pytest.raises(FileNotFoundError):
            reader.open("/nonexistent/path/slide.svs")

    @patch("services.readers.openslide_reader.openslide", create=True)
    def test_get_metadata(self, patched_openslide):  # noqa: ARG002
        """Test metadata extraction."""
        mock_slide = self._create_mock_openslide()

        mock_openslide = MagicMock()
        mock_openslide.OpenSlide.return_value = mock_slide
        mock_openslide.OpenSlide.detect_format.return_value = "aperio"
        mock_openslide.PROPERTY_NAME_MPP_X = "openslide.mpp-x"
        mock_openslide.PROPERTY_NAME_MPP_Y = "openslide.mpp-y"
        mock_openslide.PROPERTY_NAME_OBJECTIVE_POWER = "openslide.objective-power"
        mock_openslide.PROPERTY_NAME_VENDOR = "openslide.vendor"

        with patch.dict("sys.modules", {"openslide": mock_openslide}):
            reader = OpenSlideReader()
            with tempfile.NamedTemporaryFile(suffix=".svs") as tmp:
                reader.open(tmp.name)
                meta = reader.get_metadata()
                assert isinstance(meta, SlideMetadata)
                assert meta.width == 100000
                assert meta.height == 80000
                assert meta.level_count == 3
                reader.close()


# ============================================================================
# 4. BioFormatsReader Tests
# ============================================================================


class TestBioFormatsReader:
    """Test BioFormatsReader behavior when JRE is unavailable."""

    def test_can_open_returns_0_without_jre(self):
        """can_open() should return 0 when jpype is not installed."""
        assert BioFormatsReader.can_open("slide.czi") == 0
        assert BioFormatsReader.can_open("slide.nd2") == 0
        assert BioFormatsReader.can_open("slide.lif") == 0
        assert BioFormatsReader.can_open("slide.vsi") == 0

    def test_supported_formats(self):
        """supported_formats() returns expected list."""
        formats = BioFormatsReader.supported_formats()
        assert "czi" in formats
        assert "nd2" in formats
        assert "lif" in formats
        assert "vsi" in formats

    def test_open_raises_runtime_error(self):
        """open() should raise RuntimeError about JRE."""
        reader = BioFormatsReader()
        with pytest.raises(RuntimeError, match="Java Runtime"):
            reader.open("slide.czi")

    def test_read_region_raises_runtime_error(self):
        """read_region() should raise RuntimeError about JRE."""
        reader = BioFormatsReader()
        with pytest.raises(RuntimeError, match="Java Runtime"):
            reader.read_region((0, 0), 0, (256, 256))

    def test_get_metadata_raises_runtime_error(self):
        """get_metadata() should raise RuntimeError about JRE."""
        reader = BioFormatsReader()
        with pytest.raises(RuntimeError, match="Java Runtime"):
            reader.get_metadata()

    def test_close_does_not_raise(self):
        """close() should be safe even when JRE is not available."""
        reader = BioFormatsReader()
        reader.close()  # Should not raise


# ============================================================================
# 5. ReaderSelector - Picks Highest Score
# ============================================================================


class TestReaderSelectorPicking:
    """Test ReaderSelector picks the highest-scoring reader."""

    def test_picks_highest_score(self):
        """Selector should pick the reader with the highest score."""
        high_cls = _make_mock_reader("HighReader", 90)
        low_cls = _make_mock_reader("LowReader", 50)

        selector = ReaderSelector()
        selector.register(low_cls)
        selector.register(high_cls)

        reader = selector.select("test.test")
        assert type(reader).__name__ == "HighReader"
        reader.close()

    def test_skips_zero_score(self):
        """Readers with score 0 should be skipped."""
        zero_cls = _make_mock_reader("ZeroReader", 0)
        good_cls = _make_mock_reader("GoodReader", 80)

        selector = ReaderSelector()
        selector.register(zero_cls)
        selector.register(good_cls)

        reader = selector.select("test.test")
        assert type(reader).__name__ == "GoodReader"
        reader.close()


# ============================================================================
# 6. ReaderSelector - Fallback
# ============================================================================


class TestReaderSelectorFallback:
    """Test ReaderSelector fallback when first reader fails."""

    def test_fallback_when_first_fails(self):
        """When the top-scoring reader fails, fall back to the next."""
        fail_cls = _make_mock_reader("FailReader", 90, open_succeeds=False)
        backup_cls = _make_mock_reader("BackupReader", 70)

        selector = ReaderSelector()
        selector.register(fail_cls)
        selector.register(backup_cls)

        reader = selector.select("test.test")
        assert type(reader).__name__ == "BackupReader"
        reader.close()

    def test_multiple_fallbacks(self):
        """Selector should keep trying until one succeeds."""
        fail1_cls = _make_mock_reader("Fail1", 90, open_succeeds=False)
        fail2_cls = _make_mock_reader("Fail2", 80, open_succeeds=False)
        success_cls = _make_mock_reader("Success", 70)

        selector = ReaderSelector()
        selector.register(fail1_cls)
        selector.register(fail2_cls)
        selector.register(success_cls)

        reader = selector.select("test.test")
        assert type(reader).__name__ == "Success"
        reader.close()


# ============================================================================
# 7. NoCompatibleReaderError
# ============================================================================


class TestNoCompatibleReaderError:
    """Test that NoCompatibleReaderError is raised appropriately."""

    def test_no_readers_registered(self):
        """Empty selector should raise NoCompatibleReaderError."""
        selector = ReaderSelector()
        with pytest.raises(NoCompatibleReaderError, match="No reader can open"):
            selector.select("test.test")

    def test_all_readers_fail(self):
        """When all readers fail, NoCompatibleReaderError should be raised."""
        fail1_cls = _make_mock_reader("Fail1", 90, open_succeeds=False)
        fail2_cls = _make_mock_reader("Fail2", 80, open_succeeds=False)

        selector = ReaderSelector()
        selector.register(fail1_cls)
        selector.register(fail2_cls)

        with pytest.raises(NoCompatibleReaderError, match="No reader can open"):
            selector.select("test.test")

    def test_all_readers_score_zero(self):
        """When all readers score 0, NoCompatibleReaderError should be raised."""
        zero1_cls = _make_mock_reader("Zero1", 0)
        zero2_cls = _make_mock_reader("Zero2", 0)

        selector = ReaderSelector()
        selector.register(zero1_cls)
        selector.register(zero2_cls)

        with pytest.raises(NoCompatibleReaderError):
            selector.select("test.test")

    def test_error_message_includes_details(self):
        """Error message should include attempted readers and their errors."""
        fail_cls = _make_mock_reader("FailReader", 90, open_succeeds=False)

        selector = ReaderSelector()
        selector.register(fail_cls)

        with pytest.raises(NoCompatibleReaderError, match="FailReader"):
            selector.select("test.test")


# ============================================================================
# 8. OMETIFFReader Tests
# ============================================================================


class TestOMETIFFReader:
    """Test OMETIFFReader.can_open() and OME-XML parsing."""

    def test_can_open_returns_0_without_tifffile(self):
        """can_open() returns 0 when tifffile is not available."""
        with patch("services.readers.ome_tiff_reader._HAS_TIFFFILE", False):
            assert OMETIFFReader.can_open("slide.ome.tiff") == 0

    def test_can_open_returns_0_for_non_tiff(self):
        """can_open() returns 0 for non-TIFF files."""
        assert OMETIFFReader.can_open("slide.svs") == 0
        assert OMETIFFReader.can_open("slide.png") == 0

    def test_can_open_with_ome_tiff(self):
        """can_open() returns 85 for valid OME-TIFF files."""
        with (
            patch("services.readers.ome_tiff_reader._HAS_TIFFFILE", True),
            patch("services.readers.ome_tiff_reader._is_ome_tiff", return_value=True),
        ):
            assert OMETIFFReader.can_open("slide.ome.tiff") == 85
            assert OMETIFFReader.can_open("slide.ome.tif") == 85

    def test_supported_formats(self):
        """supported_formats() returns expected list."""
        formats = OMETIFFReader.supported_formats()
        assert "ome.tiff" in formats
        assert "ome.tif" in formats

    def test_parse_ome_xml_basic(self):
        """Test OME-XML parsing extracts correct dimensions."""
        xml = """<?xml version="1.0"?>
        <OME>
          <Image ID="Image:0">
            <Pixels SizeC="3" SizeZ="5" SizeT="2"
                    PhysicalSizeX="0.25" PhysicalSizeY="0.25">
            </Pixels>
          </Image>
        </OME>"""
        result = _parse_ome_xml(xml)
        assert result["channels"] == 3
        assert result["z_levels"] == 5
        assert result["timepoints"] == 2
        assert result["mpp_x"] == 0.25
        assert result["mpp_y"] == 0.25

    def test_parse_ome_xml_minimal(self):
        """Test OME-XML parsing with minimal data."""
        xml = """<?xml version="1.0"?><OME></OME>"""
        result = _parse_ome_xml(xml)
        assert result["channels"] == 1
        assert result["z_levels"] == 1
        assert result["timepoints"] == 1
        assert result["mpp_x"] is None
        assert result["mpp_y"] is None

    def test_parse_ome_xml_malformed(self):
        """Test OME-XML parsing with malformed XML returns defaults."""
        result = _parse_ome_xml("not valid xml at all")
        assert result["channels"] == 1

    def test_open_without_tifffile_raises(self):
        """open() raises RuntimeError when tifffile is not installed."""
        with patch("services.readers.ome_tiff_reader._HAS_TIFFFILE", False):
            reader = OMETIFFReader()
            with pytest.raises(RuntimeError, match="tifffile"):
                reader.open("slide.ome.tiff")

    def test_close_safe_when_not_open(self):
        """close() should not raise when reader is not open."""
        reader = OMETIFFReader()
        reader.close()  # Should not raise


# ============================================================================
# 9. OMEZarrReader Tests
# ============================================================================


class TestOMEZarrReader:
    """Test OMEZarrReader.can_open() and OME-Zarr detection."""

    def test_can_open_returns_0_without_zarr(self):
        """can_open() returns 0 when zarr is not available."""
        with patch("services.readers.ome_zarr_reader._HAS_ZARR", False):
            assert OMEZarrReader.can_open("slide.zarr") == 0

    def test_can_open_returns_0_for_non_zarr(self):
        """can_open() returns 0 for non-zarr files."""
        assert OMEZarrReader.can_open("slide.svs") == 0
        assert OMEZarrReader.can_open("slide.tiff") == 0

    def test_can_open_with_ome_zarr(self):
        """can_open() returns 85 for valid OME-Zarr directories."""
        with (
            patch("services.readers.ome_zarr_reader._HAS_ZARR", True),
            patch("services.readers.ome_zarr_reader._is_ome_zarr", return_value=True),
        ):
            assert OMEZarrReader.can_open("slide.zarr") == 85

    def test_is_ome_zarr_with_valid_dir(self):
        """_is_ome_zarr detects valid OME-Zarr directories."""
        with tempfile.TemporaryDirectory(suffix=".zarr") as tmpdir:
            zattrs = Path(tmpdir) / ".zattrs"
            zattrs.write_text(
                json.dumps({"multiscales": [{"datasets": [{"path": "0"}], "version": "0.4"}]})
            )
            assert _is_ome_zarr(tmpdir) is True

    def test_is_ome_zarr_without_multiscales(self):
        """_is_ome_zarr returns False for directories without multiscales."""
        with tempfile.TemporaryDirectory(suffix=".zarr") as tmpdir:
            zattrs = Path(tmpdir) / ".zattrs"
            zattrs.write_text(json.dumps({"other_key": "value"}))
            assert _is_ome_zarr(tmpdir) is False

    def test_is_ome_zarr_nonexistent_dir(self):
        """_is_ome_zarr returns False for nonexistent directories."""
        assert _is_ome_zarr("/nonexistent/path.zarr") is False

    def test_is_ome_zarr_regular_file(self):
        """_is_ome_zarr returns False for regular files."""
        with tempfile.NamedTemporaryFile(suffix=".zarr") as tmp:
            assert _is_ome_zarr(tmp.name) is False

    def test_supported_formats(self):
        """supported_formats() returns expected list."""
        formats = OMEZarrReader.supported_formats()
        assert "zarr" in formats
        assert "ome.zarr" in formats

    def test_open_without_zarr_raises(self):
        """open() raises RuntimeError when zarr is not installed."""
        with patch("services.readers.ome_zarr_reader._HAS_ZARR", False):
            reader = OMEZarrReader()
            with pytest.raises(RuntimeError, match="zarr"):
                reader.open("slide.zarr")

    def test_close_safe_when_not_open(self):
        """close() should not raise when reader is not open."""
        reader = OMEZarrReader()
        reader.close()  # Should not raise


# ============================================================================
# 10. Context Manager Protocol
# ============================================================================


class TestContextManagerProtocol:
    """Test that context manager protocol works correctly."""

    def test_context_manager_calls_close(self):
        """Exiting context manager should call close()."""

        class TrackingReader(ISlideReader):
            close_called = False

            def open(self, path):
                pass

            def close(self):
                TrackingReader.close_called = True

            def read_region(self, location, level, size):  # noqa: ARG002
                return np.zeros((10, 10, 3), dtype=np.uint8)

            def get_metadata(self):
                return SlideMetadata(
                    width=100, height=100, level_count=1, level_dimensions=[(100, 100)]
                )

            def get_thumbnail(self, size):  # noqa: ARG002
                return np.zeros((10, 10, 3), dtype=np.uint8)

            @property
            def dimensions(self):
                return (100, 100)

            @property
            def level_count(self):
                return 1

            @property
            def level_dimensions(self):
                return [(100, 100)]

            @classmethod
            def supported_formats(cls):
                return ["test"]

            @classmethod
            def can_open(cls, path):  # noqa: ARG003
                return 50

        with TrackingReader() as reader:
            assert reader is not None

        assert TrackingReader.close_called is True

    def test_context_manager_closes_on_exception(self):
        """Context manager should close even if an exception occurs."""

        class ErrorReader(ISlideReader):
            close_called = False

            def open(self, path):
                pass

            def close(self):
                ErrorReader.close_called = True

            def read_region(self, location, level, size):  # noqa: ARG002
                msg = "test error"
                raise ValueError(msg)

            def get_metadata(self):
                return SlideMetadata(
                    width=100, height=100, level_count=1, level_dimensions=[(100, 100)]
                )

            def get_thumbnail(self, size):  # noqa: ARG002
                return np.zeros((10, 10, 3), dtype=np.uint8)

            @property
            def dimensions(self):
                return (100, 100)

            @property
            def level_count(self):
                return 1

            @property
            def level_dimensions(self):
                return [(100, 100)]

            @classmethod
            def supported_formats(cls):
                return ["test"]

            @classmethod
            def can_open(cls, path):  # noqa: ARG003
                return 50

        with pytest.raises(ValueError, match="test error"), ErrorReader() as reader:
            reader.read_region((0, 0), 0, (256, 256))

        assert ErrorReader.close_called is True

    def test_enter_returns_self(self):
        """__enter__ should return the reader instance itself."""
        reader = OpenSlideReader()
        result = reader.__enter__()
        assert result is reader


# ============================================================================
# 11. SlideMetadata Dataclass Tests
# ============================================================================


class TestSlideMetadata:
    """Test SlideMetadata dataclass fields and defaults."""

    def test_required_fields(self):
        """Test that required fields must be provided."""
        meta = SlideMetadata(
            width=100000,
            height=80000,
            level_count=3,
            level_dimensions=[(100000, 80000), (50000, 40000), (25000, 20000)],
        )
        assert meta.width == 100000
        assert meta.height == 80000
        assert meta.level_count == 3
        assert len(meta.level_dimensions) == 3

    def test_optional_fields_default_none(self):
        """Test that optional fields default to None."""
        meta = SlideMetadata(width=100, height=100, level_count=1, level_dimensions=[(100, 100)])
        assert meta.mpp_x is None
        assert meta.mpp_y is None
        assert meta.objective_power is None
        assert meta.vendor is None
        assert meta.format_name is None

    def test_default_properties_empty_dict(self):
        """Test that properties defaults to empty dict."""
        meta = SlideMetadata(width=100, height=100, level_count=1, level_dimensions=[(100, 100)])
        assert meta.properties == {}
        assert isinstance(meta.properties, dict)

    def test_nd_defaults(self):
        """Test N-dimensional fields default to 1."""
        meta = SlideMetadata(width=100, height=100, level_count=1, level_dimensions=[(100, 100)])
        assert meta.channels == 1
        assert meta.z_levels == 1
        assert meta.timepoints == 1

    def test_ome_fields(self):
        """Test OME N-dimensional fields can be set."""
        meta = SlideMetadata(
            width=1024,
            height=1024,
            level_count=1,
            level_dimensions=[(1024, 1024)],
            channels=3,
            z_levels=10,
            timepoints=5,
        )
        assert meta.channels == 3
        assert meta.z_levels == 10
        assert meta.timepoints == 5

    def test_full_metadata(self):
        """Test creating SlideMetadata with all fields."""
        meta = SlideMetadata(
            width=100000,
            height=80000,
            level_count=4,
            level_dimensions=[(100000, 80000), (50000, 40000), (25000, 20000), (12500, 10000)],
            mpp_x=0.25,
            mpp_y=0.25,
            objective_power=40,
            vendor="Aperio",
            format_name="aperio",
            properties={"openslide.vendor": "aperio"},
            channels=1,
            z_levels=1,
            timepoints=1,
        )
        assert meta.mpp_x == 0.25
        assert meta.vendor == "Aperio"
        assert meta.objective_power == 40
        assert meta.properties["openslide.vendor"] == "aperio"

    def test_properties_independence(self):
        """Test that properties dict is independent between instances."""
        meta1 = SlideMetadata(width=100, height=100, level_count=1, level_dimensions=[(100, 100)])
        meta2 = SlideMetadata(width=200, height=200, level_count=1, level_dimensions=[(200, 200)])
        meta1.properties["key"] = "value"
        assert "key" not in meta2.properties


# ============================================================================
# 12. ReaderSelector Registration
# ============================================================================


class TestReaderSelectorRegistration:
    """Test ReaderSelector registration behavior."""

    def test_register_valid_reader(self):
        """Registering a valid ISlideReader subclass should succeed."""
        selector = ReaderSelector()
        selector.register(OpenSlideReader)
        assert len(selector._readers) == 1

    def test_register_invalid_type_raises(self):
        """Registering a non-ISlideReader should raise TypeError."""
        selector = ReaderSelector()
        with pytest.raises(TypeError, match="subclass of ISlideReader"):
            selector.register(str)  # type: ignore[arg-type]

    def test_register_same_reader_twice_is_idempotent(self):
        """Registering the same reader twice should not duplicate."""
        selector = ReaderSelector()
        selector.register(OpenSlideReader)
        selector.register(OpenSlideReader)
        assert len(selector._readers) == 1

    def test_default_selector_registers_all_readers(self):
        """default_selector() should register all available readers."""
        selector = default_selector()
        reader_names = [r.__name__ for r in selector._readers]
        assert "OpenSlideReader" in reader_names
        assert "OMETIFFReader" in reader_names
        assert "OMEZarrReader" in reader_names
        assert "BioFormatsReader" in reader_names
