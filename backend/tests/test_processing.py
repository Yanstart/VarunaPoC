"""
Tests for processing pipeline services.

Tests cover:
- BatchTileService: batch extraction, empty regions, max limit
- ColorNormalizationService: reinhard, macenko, invalid method, blank tiles
- AnnotationOutlierService: normal annotations, size outliers, timing outliers, empty list

All tests use mocked OpenSlide / numpy data — no real slides needed.
"""

import io
import zipfile
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import numpy as np
import pytest

# ============================================================================
# BatchTileService Tests
# ============================================================================


class TestBatchTileService:
    """Tests for services.batch_tiles.BatchTileService."""

    def test_extract_batch_mock_returns_zip(self):
        """Extract batch with mocked OpenSlide returns valid ZIP bytes."""
        from services.batch_tiles import BatchTileService, TileRegion

        service = BatchTileService()
        regions = [
            TileRegion(x=0, y=0, level=0, w=64, h=64),
            TileRegion(x=100, y=200, level=0, w=128, h=128),
            TileRegion(x=500, y=500, level=1, w=256, h=256),
        ]

        # Force mock mode by patching OPENSLIDE_AVAILABLE
        with patch("services.batch_tiles.OPENSLIDE_AVAILABLE", False):
            zip_bytes, result = service.extract_batch(
                slide_path="/fake/slide.svs",
                regions=regions,
                img_format="jpeg",
                quality=85,
            )

        # Verify result metadata
        assert result.tile_count == 3
        assert result.total_size_bytes == len(zip_bytes)
        assert result.processing_time_ms >= 0
        assert result.format == "zip"

        # Verify ZIP contents
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert len(names) == 3
            # Check naming pattern
            assert names[0].startswith("tile_00000_")
            assert names[0].endswith(".jpg")

    def test_extract_batch_png_format(self):
        """Extract batch with PNG format produces .png files in ZIP."""
        from services.batch_tiles import BatchTileService, TileRegion

        service = BatchTileService()
        regions = [TileRegion(x=0, y=0, level=0, w=32, h=32)]

        with patch("services.batch_tiles.OPENSLIDE_AVAILABLE", False):
            zip_bytes, _result = service.extract_batch(
                slide_path="/fake/slide.svs",
                regions=regions,
                img_format="png",
                quality=85,
            )

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert len(names) == 1
            assert names[0].endswith(".png")

    def test_extract_batch_empty_regions(self):
        """Empty regions list produces valid empty ZIP."""
        from services.batch_tiles import BatchTileService

        service = BatchTileService()

        with patch("services.batch_tiles.OPENSLIDE_AVAILABLE", False):
            zip_bytes, result = service.extract_batch(
                slide_path="/fake/slide.svs",
                regions=[],
                img_format="jpeg",
                quality=85,
            )

        assert result.tile_count == 0
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert len(zf.namelist()) == 0

    def test_extract_batch_max_regions_enforced(self):
        """Exceeding MAX_REGIONS raises ValueError."""
        from services.batch_tiles import BatchTileService, TileRegion

        service = BatchTileService()
        regions = [TileRegion(x=0, y=0)] * (service.MAX_REGIONS + 1)

        with pytest.raises(ValueError, match="Too many regions"):
            service.extract_batch(
                slide_path="/fake/slide.svs",
                regions=regions,
            )


# ============================================================================
# ColorNormalizationService Tests
# ============================================================================


class TestColorNormalizationService:
    """Tests for services.color_normalization.ColorNormalizationService."""

    def _make_tissue_tile(self, h=64, w=64):
        """Create a synthetic H&E-like tile with tissue-like colors."""
        rng = np.random.RandomState(42)
        tile = np.zeros((h, w, 3), dtype=np.uint8)
        # Simulate a mix of purple (hematoxylin) and pink (eosin)
        tile[:, :, 0] = rng.randint(100, 200, (h, w))  # R
        tile[:, :, 1] = rng.randint(50, 150, (h, w))  # G
        tile[:, :, 2] = rng.randint(100, 200, (h, w))  # B
        return tile

    def test_reinhard_normalize_same_shape(self):
        """Reinhard normalize produces output with same shape as input."""
        from services.color_normalization import ColorNormalizationService

        service = ColorNormalizationService()
        tile = self._make_tissue_tile(64, 64)

        result = service.normalize_tile(tile, method="reinhard")

        assert result.shape == tile.shape
        assert result.dtype == np.uint8

    def test_macenko_normalize_same_shape(self):
        """Macenko normalize produces output with same shape as input."""
        from services.color_normalization import ColorNormalizationService

        service = ColorNormalizationService()
        tile = self._make_tissue_tile(64, 64)

        result = service.normalize_tile(tile, method="macenko")

        assert result.shape == tile.shape
        assert result.dtype == np.uint8

    def test_vahadane_normalize_same_shape(self):
        """Vahadane (Macenko fallback) produces output with same shape."""
        from services.color_normalization import ColorNormalizationService

        service = ColorNormalizationService()
        tile = self._make_tissue_tile(64, 64)

        result = service.normalize_tile(tile, method="vahadane")

        assert result.shape == tile.shape
        assert result.dtype == np.uint8

    def test_invalid_method_raises_valueerror(self):
        """Invalid method raises ValueError."""
        from services.color_normalization import ColorNormalizationService

        service = ColorNormalizationService()
        tile = self._make_tissue_tile()

        with pytest.raises(ValueError, match="Unknown method"):
            service.normalize_tile(tile, method="nonexistent")

    def test_handles_white_blank_tile(self):
        """White/blank tile is handled gracefully without errors."""
        from services.color_normalization import ColorNormalizationService

        service = ColorNormalizationService()
        # Pure white tile
        tile = np.full((64, 64, 3), 255, dtype=np.uint8)

        # Reinhard should handle it
        result_r = service.normalize_tile(tile, method="reinhard")
        assert result_r.shape == tile.shape
        assert result_r.dtype == np.uint8

        # Macenko should handle it (returns original for blank)
        result_m = service.normalize_tile(tile, method="macenko")
        assert result_m.shape == tile.shape
        assert result_m.dtype == np.uint8

    def test_handles_empty_tile(self):
        """Empty (0-size) tile is handled gracefully."""
        from services.color_normalization import ColorNormalizationService

        service = ColorNormalizationService()
        tile = np.empty((0, 0, 3), dtype=np.uint8)

        result = service.normalize_tile(tile, method="reinhard")
        assert result.shape == tile.shape

    def test_normalize_batch(self):
        """normalize_batch processes multiple tiles and returns metadata."""
        from services.color_normalization import ColorNormalizationService

        service = ColorNormalizationService()
        tiles = [self._make_tissue_tile(32, 32) for _ in range(5)]

        normalized, result = service.normalize_batch(tiles, method="reinhard")

        assert len(normalized) == 5
        assert result.tile_count == 5
        assert result.method == "reinhard"
        assert result.processing_time_ms >= 0
        assert result.reference_stain == "default"

    def test_reinhard_with_reference(self):
        """Reinhard normalization with custom reference image."""
        from services.color_normalization import ColorNormalizationService

        service = ColorNormalizationService()
        source = self._make_tissue_tile(32, 32)

        rng = np.random.RandomState(99)
        reference = np.zeros((32, 32, 3), dtype=np.uint8)
        reference[:, :, 0] = rng.randint(150, 230, (32, 32))
        reference[:, :, 1] = rng.randint(80, 180, (32, 32))
        reference[:, :, 2] = rng.randint(130, 220, (32, 32))

        result = service.normalize_tile(source, method="reinhard", reference=reference)
        assert result.shape == source.shape
        assert result.dtype == np.uint8


# ============================================================================
# AnnotationOutlierService Tests
# ============================================================================


class TestAnnotationOutlierService:
    """Tests for services.annotation_outliers.AnnotationOutlierService."""

    def _make_polygon(self, cx, cy, size=100):
        """Create a simple square polygon annotation centered at (cx, cy)."""
        half = size / 2
        return {
            "type": "Polygon",
            "coordinates": [
                [
                    [cx - half, cy - half],
                    [cx + half, cy - half],
                    [cx + half, cy + half],
                    [cx - half, cy + half],
                    [cx - half, cy - half],
                ]
            ],
        }

    def _make_annotation(self, ann_id, cx, cy, size=100, label="tumor", **props):
        """Create a complete annotation dict."""
        return {
            "id": ann_id,
            "geometry": self._make_polygon(cx, cy, size),
            "properties": {"label": label, **props},
        }

    def test_normal_annotations_no_outliers(self):
        """Normal annotations with similar sizes produce no outliers."""
        from services.annotation_outliers import AnnotationOutlierService

        service = AnnotationOutlierService()

        annotations = [
            self._make_annotation(f"ann-{i}", cx=500 + i * 200, cy=500 + i * 200, size=100)
            for i in range(10)
        ]

        report = service.detect_outliers(annotations)

        assert report.total_annotations == 10
        assert report.outlier_count == 0
        assert len(report.outliers) == 0
        assert report.processing_time_ms >= 0

    def test_size_outlier_detected(self):
        """One very large annotation is flagged as a size outlier."""
        from services.annotation_outliers import AnnotationOutlierService

        service = AnnotationOutlierService()

        # 19 normal annotations + 1 very large one (need enough samples for
        # z-score to overcome the outlier's own influence on std)
        annotations = [
            self._make_annotation(f"ann-{i}", cx=500 + i * 200, cy=500 + i * 200, size=100)
            for i in range(19)
        ]
        # Add a massive annotation (100x larger side -> 10000x area)
        annotations.append(self._make_annotation("ann-big", cx=500, cy=500, size=10000))

        report = service.detect_outliers(annotations)

        assert report.total_annotations == 20
        assert report.outlier_count >= 1

        # The big annotation should be in the outliers
        outlier_ids = [o.annotation_id for o in report.outliers]
        assert "ann-big" in outlier_ids

        # Check that the big outlier has size category
        big_outlier = next(o for o in report.outliers if o.annotation_id == "ann-big")
        assert "size" in big_outlier.category or any("z-score" in r for r in big_outlier.reasons)
        assert big_outlier.score > 0

    def test_timing_outlier_detected(self):
        """Annotation created in < 1 second is flagged as timing outlier."""
        from services.annotation_outliers import AnnotationOutlierService

        service = AnnotationOutlierService()

        now = datetime.now(UTC)

        annotations = [
            self._make_annotation(
                "ann-fast",
                cx=500,
                cy=500,
                size=100,
                created_at=now.isoformat(),
                updated_at=(now + timedelta(seconds=0.3)).isoformat(),
            ),
            self._make_annotation(
                "ann-normal",
                cx=600,
                cy=600,
                size=100,
                created_at=now.isoformat(),
                updated_at=(now + timedelta(seconds=10)).isoformat(),
            ),
        ]

        report = service.detect_outliers(annotations)

        outlier_ids = [o.annotation_id for o in report.outliers]
        assert "ann-fast" in outlier_ids

        fast_outlier = next(o for o in report.outliers if o.annotation_id == "ann-fast")
        assert fast_outlier.category == "timing"

    def test_empty_annotations_list(self):
        """Empty annotations list produces empty report."""
        from services.annotation_outliers import AnnotationOutlierService

        service = AnnotationOutlierService()

        report = service.detect_outliers([])

        assert report.total_annotations == 0
        assert report.outlier_count == 0
        assert len(report.outliers) == 0
        assert report.processing_time_ms >= 0

    def test_position_outlier_detected(self):
        """Annotation outside slide bounds is flagged as position outlier."""
        from services.annotation_outliers import AnnotationOutlierService

        service = AnnotationOutlierService()

        annotations = [
            self._make_annotation("ann-inside", cx=500, cy=500, size=100),
            self._make_annotation("ann-outside", cx=-500, cy=-500, size=100),
        ]

        report = service.detect_outliers(
            annotations, slide_dimensions=(1000, 1000)
        )

        outlier_ids = [o.annotation_id for o in report.outliers]
        assert "ann-outside" in outlier_ids
        assert "ann-inside" not in outlier_ids

    def test_inconsistency_outlier_detected(self):
        """Annotation with different label in same region is flagged."""
        from services.annotation_outliers import AnnotationOutlierService

        service = AnnotationOutlierService()

        # 5 annotations in same grid cell with label "tumor", 1 with "normal"
        annotations = [
            self._make_annotation(f"ann-{i}", cx=500, cy=500, size=50, label="tumor")
            for i in range(5)
        ]
        annotations.append(
            self._make_annotation("ann-odd", cx=510, cy=510, size=50, label="normal")
        )

        report = service.detect_outliers(annotations)

        outlier_ids = [o.annotation_id for o in report.outliers]
        assert "ann-odd" in outlier_ids

        odd_outlier = next(o for o in report.outliers if o.annotation_id == "ann-odd")
        assert odd_outlier.category == "inconsistency"

    def test_single_annotation_no_crash(self):
        """Single annotation does not crash (no std deviation possible)."""
        from services.annotation_outliers import AnnotationOutlierService

        service = AnnotationOutlierService()

        annotations = [self._make_annotation("ann-solo", cx=500, cy=500, size=100)]

        report = service.detect_outliers(annotations)
        assert report.total_annotations == 1
        # Single annotation cannot be a size outlier (needs >= 2 for stats)
        size_outliers = [o for o in report.outliers if o.category == "size"]
        assert len(size_outliers) == 0
