"""
Format Detector Tests

Comprehensive unit tests for backend/services/format_detector.py.

Tests cover:
- Detection of MRXS (3DHistech), BIF (Ventana), SVS (Aperio), NDPI (Hamamatsu)
- Detection of unsupported files (ZVI, VSI)
- Detection of corrupted files
- The detect_format() main function dispatch
- The SlideFormat dataclass output
- The scan_directory() method
- Helper methods (_validate_with_openslide, _try_open_slide, etc.)

All file system and OpenSlide interactions are mocked since no real
slide files are available in the test environment.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from services.format_detector import FormatDetector, SlideFormat

# =========================================================================
# SlideFormat dataclass tests
# =========================================================================


class TestSlideFormat:
    """Tests for the SlideFormat dataclass."""

    def test_default_fields(self):
        """SlideFormat should have sensible defaults for optional fields."""
        sf = SlideFormat(
            name="Test",
            entry_point=Path("/fake/slide.svs"),
            is_supported=True,
        )
        assert sf.name == "Test"
        assert sf.entry_point == Path("/fake/slide.svs")
        assert sf.is_supported is True
        assert sf.joint_files == []
        assert sf.companion_dirs == []
        assert sf.metadata_files == []
        assert sf.format_string is None
        assert sf.structure_type == "unknown"
        assert sf.detection_method == ""
        assert sf.notes == ""

    def test_full_construction(self):
        """SlideFormat should store all provided fields correctly."""
        entry = Path("/slides/test.mrxs")
        companion = Path("/slides/test")
        sf = SlideFormat(
            name="MIRAX",
            entry_point=entry,
            is_supported=True,
            joint_files=[Path("/slides/test/Data0000.dat")],
            companion_dirs=[companion],
            metadata_files=[Path("/slides/test/Slidedat.ini")],
            format_string="mirax",
            structure_type="with-companion-dir",
            detection_method="test",
            notes="some notes",
        )
        assert sf.format_string == "mirax"
        assert sf.structure_type == "with-companion-dir"
        assert len(sf.joint_files) == 1
        assert len(sf.companion_dirs) == 1
        assert len(sf.metadata_files) == 1


# =========================================================================
# FormatDetector init & stats
# =========================================================================


class TestFormatDetectorInit:
    """Tests for FormatDetector initialization and bookkeeping."""

    def test_initial_state(self):
        """Detector should start with empty caches and zero stats."""
        fd = FormatDetector()
        assert fd.detected_entries == set()
        assert fd.scan_stats == {"scanned": 0, "detected": 0, "ignored": 0, "errors": 0}


# =========================================================================
# detect_format() dispatch
# =========================================================================


class TestDetectFormatDispatch:
    """Tests for the main detect_format() method."""

    def test_nonexistent_file_returns_none(self, tmp_path):
        """detect_format returns None for a path that does not exist."""
        fd = FormatDetector()
        result = fd.detect_format(tmp_path / "nonexistent.svs")
        assert result is None
        assert fd.scan_stats["scanned"] == 1

    def test_directory_returns_none(self, tmp_path):
        """detect_format returns None for a directory path."""
        fd = FormatDetector()
        result = fd.detect_format(tmp_path)
        assert result is None

    def test_unknown_extension_returns_none(self, tmp_path):
        """detect_format returns None for an unsupported extension."""
        unknown = tmp_path / "readme.txt"
        unknown.write_text("hello")
        fd = FormatDetector()
        result = fd.detect_format(unknown)
        assert result is None
        assert fd.scan_stats["ignored"] == 1

    def test_duplicate_detection_skipped(self, tmp_path):
        """detect_format skips files already detected (by resolved path)."""
        svs = tmp_path / "slide.svs"
        svs.write_bytes(b"\x00" * 100)

        fd = FormatDetector()
        # Pre-populate the detected set
        fd.detected_entries.add(str(svs.resolve()))

        result = fd.detect_format(svs)
        assert result is None

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_svs_dispatches_to_aperio(self, mock_os_cls, mock_detect, tmp_path):
        """An .svs file should dispatch to _detect_aperio."""
        svs = tmp_path / "test.svs"
        svs.write_bytes(b"\x00" * 100)

        mock_detect.return_value = "aperio"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(svs)

        assert result is not None
        assert result.name == "Aperio SVS"
        assert result.format_string == "aperio"
        assert result.structure_type == "single-file"

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_svs_rejected_by_openslide(self, mock_detect, tmp_path):
        """An .svs file rejected by OpenSlide.detect_format returns None."""
        svs = tmp_path / "notaslide.svs"
        svs.write_bytes(b"\x00" * 100)

        mock_detect.return_value = None

        fd = FormatDetector()
        result = fd.detect_format(svs)
        assert result is None
        assert fd.scan_stats["ignored"] == 1


# =========================================================================
# Aperio SVS detection
# =========================================================================


class TestDetectAperio:
    """Tests for Aperio SVS format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_valid_svs(self, mock_os_cls, mock_detect, tmp_path):
        """A valid SVS file should be detected as Aperio."""
        svs = tmp_path / "slide.svs"
        svs.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "aperio"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(svs)

        assert result is not None
        assert result.name == "Aperio SVS"
        assert result.is_supported is True
        assert result.structure_type == "single-file"
        assert result.joint_files == []
        assert fd.scan_stats["detected"] == 1

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_corrupt_svs_detected_but_unopenable(self, mock_os_cls, mock_detect, tmp_path):
        """A corrupt SVS: detect_format passes but OpenSlide() fails."""
        svs = tmp_path / "corrupt.svs"
        svs.write_bytes(b"\x00" * 50)
        mock_detect.return_value = "aperio"

        import openslide

        mock_os_cls.side_effect = openslide.OpenSlideError("corrupted TIFF")

        fd = FormatDetector()
        result = fd.detect_format(svs)

        assert result is not None
        assert result.name == "Aperio SVS"
        assert result.is_supported is False
        assert "cannot open" in result.notes


# =========================================================================
# Hamamatsu NDPI detection
# =========================================================================


class TestDetectNDPI:
    """Tests for Hamamatsu NDPI format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_valid_ndpi(self, mock_os_cls, mock_detect, tmp_path):
        """A valid NDPI should be detected as Hamamatsu."""
        ndpi = tmp_path / "slide.ndpi"
        ndpi.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "hamamatsu"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(ndpi)

        assert result is not None
        assert result.name == "Hamamatsu NDPI"
        assert result.is_supported is True
        assert result.structure_type == "single-file"
        assert result.format_string == "hamamatsu"

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_ndpi_not_recognized(self, mock_detect, tmp_path):
        """An NDPI file not recognized by OpenSlide returns None."""
        ndpi = tmp_path / "fake.ndpi"
        ndpi.write_bytes(b"\x00" * 10)
        mock_detect.return_value = None

        fd = FormatDetector()
        result = fd.detect_format(ndpi)
        assert result is None

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_ndpi_corrupt_cannot_open(self, mock_os_cls, mock_detect, tmp_path):
        """A corrupt NDPI file: detect_format passes but open fails."""
        ndpi = tmp_path / "corrupt.ndpi"
        ndpi.write_bytes(b"\x00" * 50)
        mock_detect.return_value = "hamamatsu"

        import openslide

        mock_os_cls.side_effect = openslide.OpenSlideError("bad NDPI header")

        fd = FormatDetector()
        result = fd.detect_format(ndpi)

        assert result is not None
        assert result.name == "Hamamatsu NDPI"
        assert result.is_supported is False
        assert "cannot open" in result.notes


# =========================================================================
# MIRAX (3DHistech) detection
# =========================================================================


class TestDetectMIRAX:
    """Tests for MIRAX (.mrxs) format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_valid_mrxs(self, mock_detect, tmp_path):
        """A valid MRXS with companion dir should be detected."""
        # Create MRXS file
        mrxs = tmp_path / "slide.mrxs"
        mrxs.write_bytes(b"\x00" * 50)

        # Create companion directory
        companion = tmp_path / "slide"
        companion.mkdir()
        (companion / "Slidedat.ini").write_text("[section]")
        (companion / "Data0000.dat").write_bytes(b"\x00" * 100)
        (companion / "Data0001.dat").write_bytes(b"\x00" * 100)

        mock_detect.return_value = "mirax"

        fd = FormatDetector()
        result = fd.detect_format(mrxs)

        assert result is not None
        assert result.name == "MIRAX"
        assert result.is_supported is True
        assert result.structure_type == "with-companion-dir"
        assert result.format_string == "mirax"
        assert len(result.companion_dirs) == 1
        # metadata_files should contain Slidedat.ini
        assert any("Slidedat.ini" in str(f) for f in result.metadata_files)

    def test_mrxs_missing_companion_dir(self, tmp_path):
        """MRXS without companion directory returns None."""
        mrxs = tmp_path / "orphan.mrxs"
        mrxs.write_bytes(b"\x00" * 50)

        fd = FormatDetector()
        result = fd.detect_format(mrxs)
        assert result is None

    def test_mrxs_missing_slidedat_ini(self, tmp_path):
        """MRXS with companion dir but missing Slidedat.ini returns None."""
        mrxs = tmp_path / "slide.mrxs"
        mrxs.write_bytes(b"\x00" * 50)
        companion = tmp_path / "slide"
        companion.mkdir()
        (companion / "Data0000.dat").write_bytes(b"\x00" * 100)

        fd = FormatDetector()
        result = fd.detect_format(mrxs)
        assert result is None

    def test_mrxs_missing_data_files(self, tmp_path):
        """MRXS with companion dir but no Data*.dat files returns None."""
        mrxs = tmp_path / "slide.mrxs"
        mrxs.write_bytes(b"\x00" * 50)
        companion = tmp_path / "slide"
        companion.mkdir()
        (companion / "Slidedat.ini").write_text("[section]")

        fd = FormatDetector()
        result = fd.detect_format(mrxs)
        assert result is None

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_mrxs_rejected_by_openslide(self, mock_detect, tmp_path):
        """MRXS with valid structure but rejected by OpenSlide returns None."""
        mrxs = tmp_path / "slide.mrxs"
        mrxs.write_bytes(b"\x00" * 50)
        companion = tmp_path / "slide"
        companion.mkdir()
        (companion / "Slidedat.ini").write_text("[section]")
        (companion / "Data0000.dat").write_bytes(b"\x00" * 100)

        mock_detect.return_value = None

        fd = FormatDetector()
        result = fd.detect_format(mrxs)
        assert result is None


# =========================================================================
# Ventana BIF detection
# =========================================================================


class TestDetectVentanaBIF:
    """Tests for Ventana BIF format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_valid_bif(self, mock_os_cls, mock_detect, tmp_path):
        """A valid BIF file should be detected as Ventana."""
        bif = tmp_path / "slide.bif"
        bif.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "ventana"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(bif)

        assert result is not None
        assert result.name == "Ventana BIF"
        assert result.is_supported is True
        assert result.structure_type == "single-file"

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_bif_bad_direction_error(self, mock_os_cls, mock_detect, tmp_path):
        """BIF with Bad direction attribute should be detected but unsupported."""
        bif = tmp_path / "bad.bif"
        bif.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "ventana"

        import openslide

        mock_os_cls.side_effect = openslide.OpenSlideError(
            'Bad direction attribute "LEFT"'
        )

        fd = FormatDetector()
        result = fd.detect_format(bif)

        assert result is not None
        assert result.name == "Ventana BIF"
        assert result.is_supported is False
        assert "direction" in result.notes.lower()

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_bif_generic_openslide_error(self, mock_os_cls, mock_detect, tmp_path):
        """BIF with generic OpenSlide error should be detected but unsupported."""
        bif = tmp_path / "error.bif"
        bif.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "ventana"

        import openslide

        mock_os_cls.side_effect = openslide.OpenSlideError("some other error")

        fd = FormatDetector()
        result = fd.detect_format(bif)

        assert result is not None
        assert result.is_supported is False

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_bif_unexpected_error(self, mock_os_cls, mock_detect, tmp_path):
        """BIF with unexpected exception should be detected but unsupported."""
        bif = tmp_path / "crash.bif"
        bif.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "ventana"
        mock_os_cls.side_effect = RuntimeError("segfault-like")

        fd = FormatDetector()
        result = fd.detect_format(bif)

        assert result is not None
        assert result.is_supported is False
        assert "Unexpected error" in result.notes

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_bif_not_recognized(self, mock_detect, tmp_path):
        """BIF not recognized by OpenSlide returns None."""
        bif = tmp_path / "fake.bif"
        bif.write_bytes(b"\x00" * 10)
        mock_detect.return_value = None

        fd = FormatDetector()
        result = fd.detect_format(bif)
        assert result is None


# =========================================================================
# Hamamatsu VMS detection
# =========================================================================


class TestDetectHamamatsuVMS:
    """Tests for Hamamatsu VMS format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_valid_vms(self, mock_detect, tmp_path):
        """A valid VMS with JPEG joints should be detected."""
        vms = tmp_path / "slide.vms"
        vms.write_text("[Virtual Microscope Specimen]\nkey=value\n")

        # Create joint JPEG files
        (tmp_path / "slide0_0.jpg").write_bytes(b"\xff\xd8" + b"\x00" * 50)
        (tmp_path / "slide1_0.jpg").write_bytes(b"\xff\xd8" + b"\x00" * 50)

        mock_detect.return_value = "hamamatsu"

        fd = FormatDetector()
        result = fd.detect_format(vms)

        assert result is not None
        assert result.name == "Hamamatsu VMS"
        assert result.is_supported is True
        assert result.structure_type == "multi-file"
        assert len(result.joint_files) >= 2

    def test_vms_not_ini_format(self, tmp_path):
        """VMS file without INI section returns None."""
        vms = tmp_path / "notini.vms"
        vms.write_text("random content")

        fd = FormatDetector()
        result = fd.detect_format(vms)
        assert result is None

    def test_vms_no_jpeg_joints(self, tmp_path):
        """VMS file with valid INI but no JPEG joints returns None."""
        vms = tmp_path / "slide.vms"
        vms.write_text("[Virtual Microscope Specimen]\nkey=value\n")

        # No .jpg files created -- code returns None before calling OpenSlide

        fd = FormatDetector()
        result = fd.detect_format(vms)
        assert result is None

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_vms_with_opt_file(self, mock_detect, tmp_path):
        """VMS with .opt file should include it in joint_files."""
        vms = tmp_path / "slide.vms"
        vms.write_text("[Virtual Microscope Specimen]\nkey=value\n")
        (tmp_path / "slide0_0.jpg").write_bytes(b"\xff\xd8" + b"\x00" * 50)
        (tmp_path / "slide.opt").write_bytes(b"\x00" * 20)

        mock_detect.return_value = "hamamatsu"

        fd = FormatDetector()
        result = fd.detect_format(vms)

        assert result is not None
        assert any(".opt" in str(f) for f in result.joint_files)

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_vms_macro_excluded(self, mock_detect, tmp_path):
        """VMS should exclude _macro and _map JPEG files."""
        vms = tmp_path / "slide.vms"
        vms.write_text("[Virtual Microscope Specimen]\nkey=value\n")
        (tmp_path / "slide0_0.jpg").write_bytes(b"\xff\xd8" + b"\x00" * 50)
        (tmp_path / "slide_macro.jpg").write_bytes(b"\xff\xd8" + b"\x00" * 50)
        (tmp_path / "slide_map.jpg").write_bytes(b"\xff\xd8" + b"\x00" * 50)

        mock_detect.return_value = "hamamatsu"

        fd = FormatDetector()
        result = fd.detect_format(vms)

        assert result is not None
        # Only the non-macro/map JPEG should be a joint tile
        joint_names = [f.name for f in result.joint_files if f.suffix == ".jpg"]
        assert "slide_macro.jpg" not in joint_names
        assert "slide_map.jpg" not in joint_names


# =========================================================================
# Hamamatsu VMU detection
# =========================================================================


class TestDetectHamamatsuVMU:
    """Tests for Hamamatsu VMU format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_valid_vmu(self, mock_detect, tmp_path):
        """A valid VMU with NGR joints should be detected."""
        vmu = tmp_path / "slide.vmu"
        vmu.write_text("[Uncompressed Virtual Microscope Specimen]\nkey=value\n")
        (tmp_path / "slide0_0.ngr").write_bytes(b"\x00" * 50)

        mock_detect.return_value = "hamamatsu"

        fd = FormatDetector()
        result = fd.detect_format(vmu)

        assert result is not None
        assert result.name == "Hamamatsu VMU"
        assert result.structure_type == "multi-file"

    def test_vmu_not_ini_format(self, tmp_path):
        """VMU file without correct INI section returns None."""
        vmu = tmp_path / "notini.vmu"
        vmu.write_text("random")

        fd = FormatDetector()
        result = fd.detect_format(vmu)
        assert result is None

    def test_vmu_no_ngr_joints(self, tmp_path):
        """VMU file with valid INI but no NGR joints returns None."""
        vmu = tmp_path / "slide.vmu"
        vmu.write_text("[Uncompressed Virtual Microscope Specimen]\nkey=value\n")

        fd = FormatDetector()
        result = fd.detect_format(vmu)
        assert result is None


# =========================================================================
# Unsupported formats (ZVI, VSI)
# =========================================================================


class TestUnsupportedFormats:
    """Tests for formats explicitly detected but marked unsupported."""

    def test_zvi_detected_but_unsupported(self, tmp_path):
        """ZVI files should be detected but marked as unsupported."""
        zvi = tmp_path / "slide.zvi"
        zvi.write_bytes(b"\x00" * 50)

        fd = FormatDetector()
        result = fd.detect_format(zvi)

        assert result is not None
        assert result.name == "Zeiss ZVI"
        assert result.is_supported is False
        assert result.format_string is None
        assert "NOT SUPPORTED" in result.notes

    def test_vsi_detected_but_unsupported(self, tmp_path):
        """VSI files should be detected but marked as unsupported."""
        vsi = tmp_path / "slide.vsi"
        vsi.write_bytes(b"\x00" * 50)

        fd = FormatDetector()
        result = fd.detect_format(vsi)

        assert result is not None
        assert result.name == "Olympus VSI"
        assert result.is_supported is False
        assert "NOT SUPPORTED" in result.notes

    def test_vsi_with_companion_dir(self, tmp_path):
        """VSI with _name_ companion directory should detect the ETS files."""
        vsi = tmp_path / "slide.vsi"
        vsi.write_bytes(b"\x00" * 50)
        companion = tmp_path / "_slide_"
        companion.mkdir()
        (companion / "frame0.ets").write_bytes(b"\x00" * 50)
        (companion / "frame1.ets").write_bytes(b"\x00" * 50)

        fd = FormatDetector()
        result = fd.detect_format(vsi)

        assert result is not None
        assert result.structure_type == "with-companion-dir"
        assert len(result.companion_dirs) == 1
        assert "2 ETS" in result.notes


# =========================================================================
# Zeiss CZI detection
# =========================================================================


class TestDetectZeissCZI:
    """Tests for Zeiss CZI format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_valid_czi_detected_by_openslide(self, mock_os_cls, mock_detect, tmp_path):
        """CZI detected and openable by OpenSlide should be supported."""
        czi = tmp_path / "slide.czi"
        czi.write_bytes(b"ZISRAWFILE" + b"\x00" * 50)
        mock_detect.return_value = "zeiss"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(czi)

        assert result is not None
        assert result.name == "Zeiss CZI"
        assert result.is_supported is True

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_czi_detected_by_signature_only(self, mock_detect, tmp_path):
        """CZI with valid signature but not recognized by OpenSlide."""
        czi = tmp_path / "slide.czi"
        czi.write_bytes(b"ZISRAWFILE" + b"\x00" * 50)
        mock_detect.return_value = None

        fd = FormatDetector()
        result = fd.detect_format(czi)

        assert result is not None
        assert result.name == "Zeiss CZI"
        assert result.is_supported is False
        assert "cannot open" in result.notes.lower()

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    def test_czi_no_signature_no_openslide(self, mock_detect, tmp_path):
        """CZI without valid signature and not recognized returns None."""
        czi = tmp_path / "fake.czi"
        czi.write_bytes(b"\x00" * 50)
        mock_detect.return_value = None

        fd = FormatDetector()
        result = fd.detect_format(czi)
        assert result is None

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_czi_openslide_detects_but_cannot_open(self, mock_os_cls, mock_detect, tmp_path):
        """CZI detected by OpenSlide but fails to open (missing codec)."""
        czi = tmp_path / "nocodec.czi"
        czi.write_bytes(b"ZISRAWFILE" + b"\x00" * 50)
        mock_detect.return_value = "zeiss"
        mock_os_cls.side_effect = RuntimeError("missing JPEG XR codec")

        fd = FormatDetector()
        result = fd.detect_format(czi)

        assert result is not None
        assert result.name == "Zeiss CZI"
        assert result.is_supported is False


# =========================================================================
# Leica SCN detection
# =========================================================================


class TestDetectLeicaSCN:
    """Tests for Leica SCN format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_valid_scn(self, mock_os_cls, mock_detect, tmp_path):
        """A valid SCN file should be detected as Leica."""
        scn = tmp_path / "slide.scn"
        scn.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "leica"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(scn)

        assert result is not None
        assert result.name == "Leica SCN"
        assert result.is_supported is True


# =========================================================================
# TIFF variant detection
# =========================================================================


class TestDetectTIFFVariant:
    """Tests for TIFF variant detection (aperio, ventana, trestle, generic)."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_aperio_tiff(self, mock_os_cls, mock_detect, tmp_path):
        """TIFF recognized as aperio should return Aperio TIFF."""
        tif = tmp_path / "slide.tif"
        tif.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "aperio"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(tif)

        assert result is not None
        assert result.name == "Aperio TIFF"

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_generic_tiff(self, mock_os_cls, mock_detect, tmp_path):
        """TIFF recognized as generic-tiff should return Generic Pyramidal TIFF."""
        tiff = tmp_path / "slide.tiff"
        tiff.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "generic-tiff"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(tiff)

        assert result is not None
        assert result.name == "Generic Pyramidal TIFF"

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_trestle_tiff_with_adjacent(self, mock_os_cls, mock_detect, tmp_path):
        """Trestle TIFF should detect adjacent overlap files."""
        tif = tmp_path / "slide.tif"
        tif.write_bytes(b"\x00" * 100)
        # Adjacent trestle overlap files
        (tmp_path / "slide.tif-1b").write_bytes(b"\x00" * 50)
        (tmp_path / "slide.tif-2b").write_bytes(b"\x00" * 50)

        mock_detect.return_value = "trestle"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(tif)

        assert result is not None
        assert result.name == "Trestle TIFF"
        assert "adjacent" in result.notes


# =========================================================================
# DICOM detection
# =========================================================================


class TestDetectDICOM:
    """Tests for DICOM format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_valid_dicom(self, mock_os_cls, mock_detect, tmp_path):
        """A valid DICOM file should be detected."""
        dcm = tmp_path / "slide.dcm"
        dcm.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "dicom"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(dcm)

        assert result is not None
        assert result.name == "DICOM"
        assert result.is_supported is True

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_dicom_unexpected_image_error(self, mock_os_cls, mock_detect, tmp_path):
        """DICOM with 'unexpected image' error should be unsupported."""
        dcm = tmp_path / "multi.dcm"
        dcm.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "dicom"

        import openslide

        mock_os_cls.side_effect = openslide.OpenSlideError("unexpected image in frame")

        fd = FormatDetector()
        result = fd.detect_format(dcm)

        assert result is not None
        assert result.is_supported is False


# =========================================================================
# Sakura detection
# =========================================================================


class TestDetectSakura:
    """Tests for Sakura format detection."""

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_valid_sakura(self, mock_os_cls, mock_detect, tmp_path):
        """A valid Sakura file should be detected."""
        svslide = tmp_path / "slide.svslide"
        svslide.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "sakura"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        result = fd.detect_format(svslide)

        assert result is not None
        assert result.name == "Sakura"
        assert result.is_supported is True


# =========================================================================
# Helper methods
# =========================================================================


class TestHelperMethods:
    """Tests for internal helper methods."""

    def test_validate_with_openslide_returns_format_string(self, tmp_path):
        """_validate_with_openslide should return format string on success."""
        fd = FormatDetector()
        p = tmp_path / "slide.svs"

        with patch("services.format_detector.openslide.OpenSlide.detect_format") as m:
            m.return_value = "aperio"
            result = fd._validate_with_openslide(p)
            assert result == "aperio"

    def test_validate_with_openslide_returns_none_on_failure(self, tmp_path):
        """_validate_with_openslide should return None and increment errors on exception."""
        fd = FormatDetector()
        p = tmp_path / "slide.svs"

        with patch("services.format_detector.openslide.OpenSlide.detect_format") as m:
            m.side_effect = Exception("library error")
            result = fd._validate_with_openslide(p)
            assert result is None
            assert fd.scan_stats["errors"] == 1

    def test_try_open_slide_success(self, tmp_path):
        """_try_open_slide returns (True, '') on successful open."""
        fd = FormatDetector()
        p = tmp_path / "slide.svs"

        with patch("services.format_detector.openslide.OpenSlide") as m:
            mock_slide = MagicMock()
            m.return_value = mock_slide
            ok, msg = fd._try_open_slide(p)
            assert ok is True
            assert msg == ""
            mock_slide.close.assert_called_once()

    def test_try_open_slide_openslide_error(self, tmp_path):
        """_try_open_slide returns (False, message) on OpenSlideError."""
        fd = FormatDetector()
        p = tmp_path / "slide.svs"

        import openslide

        with patch("services.format_detector.openslide.OpenSlide") as m:
            m.side_effect = openslide.OpenSlideError("corrupt")
            ok, msg = fd._try_open_slide(p)
            assert ok is False
            assert "corrupt" in msg

    def test_try_open_slide_unexpected_error(self, tmp_path):
        """_try_open_slide returns (False, message) on unexpected error."""
        fd = FormatDetector()
        p = tmp_path / "slide.svs"

        with patch("services.format_detector.openslide.OpenSlide") as m:
            m.side_effect = RuntimeError("segfault")
            ok, msg = fd._try_open_slide(p)
            assert ok is False
            assert "segfault" in msg

    def test_is_vms_ini_file_valid(self, tmp_path):
        """_is_vms_ini_file returns True for valid VMS INI."""
        fd = FormatDetector()
        f = tmp_path / "slide.vms"
        f.write_text("[Virtual Microscope Specimen]\nkey=value\n")
        assert fd._is_vms_ini_file(f) is True

    def test_is_vms_ini_file_invalid(self, tmp_path):
        """_is_vms_ini_file returns False for non-VMS content."""
        fd = FormatDetector()
        f = tmp_path / "slide.vms"
        f.write_text("not an ini file")
        assert fd._is_vms_ini_file(f) is False

    def test_is_vmu_ini_file_valid(self, tmp_path):
        """_is_vmu_ini_file returns True for valid VMU INI."""
        fd = FormatDetector()
        f = tmp_path / "slide.vmu"
        f.write_text("[Uncompressed Virtual Microscope Specimen]\nkey=value\n")
        assert fd._is_vmu_ini_file(f) is True

    def test_is_vmu_ini_file_invalid(self, tmp_path):
        """_is_vmu_ini_file returns False for non-VMU content."""
        fd = FormatDetector()
        f = tmp_path / "slide.vmu"
        f.write_text("wrong content")
        assert fd._is_vmu_ini_file(f) is False


# =========================================================================
# scan_directory tests
# =========================================================================


class TestScanDirectory:
    """Tests for the scan_directory method."""

    def test_scan_empty_directory(self, tmp_path):
        """Scanning an empty directory returns empty list."""
        fd = FormatDetector()
        results = fd.scan_directory(tmp_path)
        assert results == []
        assert fd.scan_stats["scanned"] == 0

    def test_scan_directory_skips_non_slide_files(self, tmp_path):
        """Scanning should ignore non-slide files."""
        (tmp_path / "readme.txt").write_text("hello")
        (tmp_path / "data.csv").write_text("a,b,c")

        fd = FormatDetector()
        results = fd.scan_directory(tmp_path)
        assert results == []
        assert fd.scan_stats["ignored"] == 2

    @patch("services.format_detector.openslide.OpenSlide.detect_format")
    @patch("services.format_detector.openslide.OpenSlide")
    def test_scan_directory_finds_svs(self, mock_os_cls, mock_detect, tmp_path):
        """Scanning should find valid SVS files."""
        svs = tmp_path / "slide.svs"
        svs.write_bytes(b"\x00" * 100)
        mock_detect.return_value = "aperio"
        mock_slide = MagicMock()
        mock_os_cls.return_value = mock_slide

        fd = FormatDetector()
        results = fd.scan_directory(tmp_path)

        assert len(results) == 1
        assert results[0].name == "Aperio SVS"

    def test_scan_directory_non_recursive(self, tmp_path):
        """Non-recursive scan should not descend into subdirectories."""
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "readme.txt").write_text("hello")

        fd = FormatDetector()
        fd.scan_directory(tmp_path, recursive=False)
        assert fd.scan_stats["scanned"] == 0

    def test_scan_resets_stats(self, tmp_path):
        """Each scan_directory call should reset stats."""
        fd = FormatDetector()
        fd.scan_stats["scanned"] = 99
        fd.scan_directory(tmp_path)
        assert fd.scan_stats["scanned"] == 0

    def test_scan_includes_unsupported(self, tmp_path):
        """scan_directory should include unsupported formats (e.g. ZVI)."""
        zvi = tmp_path / "old.zvi"
        zvi.write_bytes(b"\x00" * 50)

        fd = FormatDetector()
        results = fd.scan_directory(tmp_path)

        assert len(results) == 1
        assert results[0].is_supported is False
        assert results[0].name == "Zeiss ZVI"
