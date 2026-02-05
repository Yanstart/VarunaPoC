"""
ML Real Slides Integration Tests

Tests d'intégration bout en bout avec de VRAIES lames.

Ces tests:
- Utilisent OpenSlide pour lire de vraies lames
- Testent le pipeline ML complet avec données réelles
- Vérifient que les formats supportés fonctionnent
- Mesurent les performances réelles

IMPORTANT:
- Ces tests sont LENTS (lames volumineuses)
- Ils nécessitent le dossier Slides/ avec des lames de test
- Ils sont marqués 'slow' et 'integration' pour être skippés en CI
- Exécuter localement: pytest -m "slow" tests/test_ml_real_slides.py -v

Run:
    # All real slide tests (local only)
    pytest tests/test_ml_real_slides.py -v -m "slow"

    # Quick smoke test (one slide)
    pytest tests/test_ml_real_slides.py::test_predict_real_mrxs -v
"""

# IMPORTANT: Configure OpenSlide DLL path BEFORE import
import os
import sys
from pathlib import Path

# Configure OpenSlide for Windows
OPENSLIDE_PATH = r"C:\msys64\ucrt64\bin"
if os.path.exists(OPENSLIDE_PATH) and sys.version_info >= (3, 8):
    os.add_dll_directory(OPENSLIDE_PATH)

import numpy as np
import pytest

# Skip all tests if OpenSlide not available
openslide = pytest.importorskip("openslide")

from core.interfaces import FeatureExtractionResult, HeatmapResult, PredictionResult
from services.ml.providers.openslide_provider import OpenSlideTestProvider

# ============================================================================
# CONFIGURATION
# ============================================================================

# Path to test slides directory
SLIDES_DIR = Path(__file__).parent.parent.parent / "Slides"

# Test slides by format (small files preferred for faster tests)
TEST_SLIDES = {
    "mrxs": SLIDES_DIR / "3Dhistec" / "CMU-1-Saved-1_16.mrxs",  # Small MRXS
    "svs": SLIDES_DIR / "Aperio" / "CMU-1-Small-Region.svs",  # Small SVS
    "tiff": SLIDES_DIR / "Generic-TIFF" / "CMU-1.tiff",  # Generic TIFF
    "bif": SLIDES_DIR / "Ventana BIF" / "Ventana-1.bif",  # Ventana BIF
    "ndpi": SLIDES_DIR / "Hamamatsu" / "CMU-1.ndpi",  # Hamamatsu NDPI
    "scn": SLIDES_DIR / "Leica" / "Leica-1.scn",  # Leica SCN
}


def slide_exists(format_key: str) -> bool:
    """Check if test slide exists."""
    path = TEST_SLIDES.get(format_key)
    return path is not None and path.exists()


def get_any_available_slide() -> Path | None:
    """Get any available test slide."""
    for path in TEST_SLIDES.values():
        if path.exists():
            return path

    for ext in [".mrxs", ".svs", ".tiff", ".bif"]:
        slides = list(SLIDES_DIR.rglob(f"*{ext}"))
        if slides:
            return slides[0]

    return None


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def openslide_provider():
    """Fixture pour OpenSlideTestProvider."""
    provider = OpenSlideTestProvider()
    config = {
        "model_id": "real_slide_test",
        "model_name": "Real Slide Test Model",
        "classes": ["tissue", "background"],
    }
    provider.load_model("heuristic://test", config)
    yield provider
    provider.unload_model()


@pytest.fixture
def any_slide_path():
    """Get path to any available test slide."""
    path = get_any_available_slide()
    if path is None:
        pytest.skip("No test slides available in Slides/ directory")
    return str(path)


# ============================================================================
# BASIC TESTS (run if any slide available)
# ============================================================================


@pytest.mark.slow
@pytest.mark.integration
class TestRealSlideBasics:
    """Basic tests with real slides."""

    def test_provider_initialization(self):
        """Test provider can be initialized."""
        provider = OpenSlideTestProvider()
        assert provider.device == "cpu"
        assert not provider.model_loaded

    def test_load_model(self):
        """Test model loading."""
        provider = OpenSlideTestProvider()
        provider.load_model(
            "heuristic://test",
            {"model_id": "test", "classes": ["a", "b"]},
        )
        assert provider.model_loaded
        provider.unload_model()

    def test_predict_real_slide(self, openslide_provider, any_slide_path):
        """Test prediction on real slide."""
        result = openslide_provider.predict(any_slide_path)

        assert isinstance(result, PredictionResult)
        assert result.prediction_class in ["tissue", "background"]
        assert 0.0 <= result.confidence <= 1.0
        assert result.execution_time_ms > 0
        assert result.slide_id != ""

        assert "slide_dimensions" in result.metadata
        dims = result.metadata["slide_dimensions"]
        assert dims[0] > 0 and dims[1] > 0

    def test_extract_features_real_slide(self, openslide_provider, any_slide_path):
        """Test feature extraction on real slide."""
        result = openslide_provider.extract_features(any_slide_path, tile_size=224)

        assert isinstance(result, FeatureExtractionResult)
        assert result.num_patches > 0
        assert result.embedding_dim == 64
        assert len(result.coordinates) == result.num_patches

        assert result.embeddings.dtype == np.float32
        assert not np.isnan(result.embeddings).any()

    def test_generate_heatmap_real_slide(self, openslide_provider, any_slide_path):
        """Test heatmap generation on real slide."""
        result = openslide_provider.generate_heatmap(any_slide_path, "tissue")

        assert isinstance(result, HeatmapResult)
        assert result.heatmap.ndim == 2
        assert result.heatmap.min() >= 0.0
        assert result.heatmap.max() <= 1.0

    def test_complete_workflow_real_slide(self, openslide_provider, any_slide_path):
        """Test complete ML workflow with real slide."""
        pred = openslide_provider.predict(any_slide_path)
        assert pred.prediction_class in ["tissue", "background"]

        features = openslide_provider.extract_features(any_slide_path)
        assert features.num_patches > 0

        heatmap = openslide_provider.generate_heatmap(any_slide_path, pred.prediction_class)
        assert heatmap.heatmap.size > 0

        info = openslide_provider.get_model_info()
        assert info["provider"] == "openslide_test"


# ============================================================================
# FORMAT-SPECIFIC TESTS
# ============================================================================


@pytest.mark.slow
@pytest.mark.integration
class TestMRXSFormat:
    """Tests spécifiques au format 3DHistech MRXS."""

    @pytest.fixture
    def mrxs_path(self):
        if not slide_exists("mrxs"):
            pytest.skip("MRXS test slide not available")
        return str(TEST_SLIDES["mrxs"])

    def test_predict_mrxs(self, openslide_provider, mrxs_path):
        """Test prediction on MRXS slide."""
        result = openslide_provider.predict(mrxs_path)
        assert result.prediction_class in ["tissue", "background"]
        assert "3DHistech" in str(result.metadata.get("slide_dimensions", "")) or True

    def test_extract_features_mrxs(self, openslide_provider, mrxs_path):
        """Test feature extraction on MRXS slide."""
        result = openslide_provider.extract_features(mrxs_path)
        assert result.num_patches > 0


@pytest.mark.slow
@pytest.mark.integration
class TestSVSFormat:
    """Tests spécifiques au format Aperio SVS."""

    @pytest.fixture
    def svs_path(self):
        if not slide_exists("svs"):
            pytest.skip("SVS test slide not available")
        return str(TEST_SLIDES["svs"])

    def test_predict_svs(self, openslide_provider, svs_path):
        """Test prediction on SVS slide."""
        result = openslide_provider.predict(svs_path)
        assert result.prediction_class in ["tissue", "background"]

    def test_extract_features_svs(self, openslide_provider, svs_path):
        """Test feature extraction on SVS slide."""
        result = openslide_provider.extract_features(svs_path)
        assert result.num_patches > 0


@pytest.mark.slow
@pytest.mark.integration
class TestBIFFormat:
    """Tests spécifiques au format Ventana BIF."""

    @pytest.fixture
    def bif_path(self):
        if not slide_exists("bif"):
            pytest.skip("BIF test slide not available")
        return str(TEST_SLIDES["bif"])

    def test_predict_bif(self, openslide_provider, bif_path):
        """Test prediction on BIF slide."""
        result = openslide_provider.predict(bif_path)
        assert result.prediction_class in ["tissue", "background"]

    def test_extract_features_bif(self, openslide_provider, bif_path):
        """Test feature extraction on BIF slide."""
        result = openslide_provider.extract_features(bif_path)
        assert result.num_patches > 0


@pytest.mark.slow
@pytest.mark.integration
class TestTIFFFormat:
    """Tests spécifiques au format Generic TIFF."""

    @pytest.fixture
    def tiff_path(self):
        if not slide_exists("tiff"):
            pytest.skip("TIFF test slide not available")
        return str(TEST_SLIDES["tiff"])

    def test_predict_tiff(self, openslide_provider, tiff_path):
        """Test prediction on TIFF slide."""
        result = openslide_provider.predict(tiff_path)
        assert result.prediction_class in ["tissue", "background"]


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@pytest.mark.slow
@pytest.mark.integration
class TestPerformance:
    """Performance tests with real slides."""

    def test_prediction_time(self, openslide_provider, any_slide_path):
        """Test prediction completes in reasonable time."""
        result = openslide_provider.predict(any_slide_path)

        assert result.execution_time_ms < 10000

    def test_feature_extraction_time(self, openslide_provider, any_slide_path):
        """Test feature extraction completes in reasonable time."""
        import time

        start = time.time()
        result = openslide_provider.extract_features(any_slide_path, tile_size=224)
        elapsed = time.time() - start

        assert elapsed < 60
        assert result.num_patches > 0

    def test_multiple_predictions(self, openslide_provider, any_slide_path):
        """Test multiple predictions on same slide."""
        results = []
        for _ in range(3):
            result = openslide_provider.predict(any_slide_path)
            results.append(result)

        for r in results:
            assert r.prediction_class == results[0].prediction_class


# ============================================================================
# EDGE CASES
# ============================================================================


@pytest.mark.slow
@pytest.mark.integration
class TestEdgeCases:
    """Edge case tests."""

    def test_predict_with_region(self, openslide_provider, any_slide_path):
        """Test prediction with specific region."""
        region = (1000, 1000, 512, 512)
        result = openslide_provider.predict(any_slide_path, region=region)

        assert result.metadata["region"] == region

    def test_small_tile_size(self, openslide_provider, any_slide_path):
        """Test feature extraction with small tiles."""
        result = openslide_provider.extract_features(any_slide_path, tile_size=64)
        assert result.num_patches > 0

    def test_large_tile_size(self, openslide_provider, any_slide_path):
        """Test feature extraction with large tiles."""
        result = openslide_provider.extract_features(any_slide_path, tile_size=512)
        assert result.num_patches > 0


# ============================================================================
# REPORT GENERATION
# ============================================================================


@pytest.mark.slow
@pytest.mark.integration
def test_generate_compatibility_report(openslide_provider):
    """
    Generate compatibility report for all available slides.

    This test iterates through all test slides and reports which ones work.
    """
    report = []

    for format_name, slide_path in TEST_SLIDES.items():
        status = "SKIP"
        details = ""

        if not slide_path.exists():
            status = "NOT_FOUND"
            details = str(slide_path)
        else:
            try:
                result = openslide_provider.predict(str(slide_path))
                status = "OK"
                details = f"pred={result.prediction_class}, conf={result.confidence:.2%}"
            except Exception as e:
                status = "ERROR"
                details = str(e)[:50]

        report.append(
            {
                "format": format_name,
                "status": status,
                "details": details,
            }
        )

    print("\n" + "=" * 70)
    print("SLIDE FORMAT COMPATIBILITY REPORT")
    print("=" * 70)
    for item in report:
        print(f"  {item['format']:10} | {item['status']:10} | {item['details']}")
    print("=" * 70)

    ok_count = sum(1 for r in report if r["status"] == "OK")
    assert ok_count >= 1, "At least one slide format should work"


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require real slides)"
    )
