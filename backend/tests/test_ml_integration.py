"""
ML Integration Tests

Tests de l'intégration ML avec Mock Provider (pas besoin de Slideflow).

Run:
    pytest backend/tests/test_ml_integration.py -v
"""

import numpy as np
import pytest

from core.exceptions import MLModelNotLoadedError
from core.interfaces import FeatureExtractionResult, HeatmapResult, PredictionResult
from services.ml.providers import MockProvider

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_provider():
    """Fixture pour MockProvider."""
    return MockProvider(seed=42)


@pytest.fixture
def loaded_mock_provider():
    """Fixture pour MockProvider avec modèle chargé."""
    provider = MockProvider(seed=42)
    config = {
        "model_id": "test_model",
        "model_name": "Test Model",
        "version": "1.0.0",
        "classes": ["benign", "malignant"],
        "embedding_dim": 512,
    }
    provider.load_model("mock://test_model", config)
    return provider


# ============================================================================
# TEST MODEL LOADING
# ============================================================================


def test_load_model(mock_provider):
    """Test chargement modèle."""
    config = {"model_id": "test_model", "classes": ["class_0", "class_1"]}

    # Before loading
    assert not mock_provider.model_loaded

    # Load
    mock_provider.load_model("mock://test_model", config)

    # After loading
    assert mock_provider.model_loaded
    assert mock_provider.model_config["model_id"] == "test_model"


def test_unload_model(loaded_mock_provider):
    """Test déchargement modèle."""
    assert loaded_mock_provider.model_loaded

    # Unload
    loaded_mock_provider.unload_model()

    assert not loaded_mock_provider.model_loaded
    assert loaded_mock_provider.model is None


def test_model_info(loaded_mock_provider):
    """Test récupération info modèle."""
    info = loaded_mock_provider.get_model_info()

    assert info["model_id"] == "test_model"
    assert info["model_name"] == "Test Model"
    assert info["version"] == "1.0.0"
    assert info["classes"] == ["benign", "malignant"]
    assert info["device"] == "cpu"
    assert info["provider"] == "mock"
    assert info["mock"] is True


def test_model_info_not_loaded(mock_provider):
    """Test erreur si model_info appelé sans modèle chargé."""
    with pytest.raises(MLModelNotLoadedError):
        mock_provider.get_model_info()


# ============================================================================
# TEST PREDICTION
# ============================================================================


def test_predict_basic(loaded_mock_provider):
    """Test prédiction basique."""
    result = loaded_mock_provider.predict("test_slide.mrxs")

    # Check type
    assert isinstance(result, PredictionResult)

    # Check attributes
    assert result.prediction_class in ["benign", "malignant"]
    assert 0.0 <= result.confidence <= 1.0
    assert 0.0 <= result.uncertainty <= 1.0
    assert result.execution_time_ms > 0
    assert result.model_id == "test_model"
    assert result.slide_id == "test_slide"

    # Check probabilities
    assert "benign" in result.probabilities
    assert "malignant" in result.probabilities
    prob_sum = sum(result.probabilities.values())
    assert 0.98 <= prob_sum <= 1.02  # Allow small floating point error


def test_predict_with_region(loaded_mock_provider):
    """Test prédiction avec région."""
    region = (1000, 1000, 2000, 2000)
    result = loaded_mock_provider.predict("test_slide.mrxs", region=region)

    assert isinstance(result, PredictionResult)
    assert result.metadata["region"] == region


def test_predict_reproducible(loaded_mock_provider):
    """Test reproductibilité prédictions (même seed)."""
    result1 = loaded_mock_provider.predict("test_slide.mrxs")
    result2 = loaded_mock_provider.predict("test_slide.mrxs")

    # Avec même seed, résultats devraient être identiques
    assert result1.prediction_class == result2.prediction_class
    assert result1.confidence == pytest.approx(result2.confidence, abs=0.01)


def test_predict_not_loaded(mock_provider):
    """Test erreur si predict appelé sans modèle chargé."""
    with pytest.raises(MLModelNotLoadedError):
        mock_provider.predict("test_slide.mrxs")


# ============================================================================
# TEST FEATURE EXTRACTION
# ============================================================================


def test_extract_features_basic(loaded_mock_provider):
    """Test extraction features basique."""
    result = loaded_mock_provider.extract_features("test_slide.mrxs")

    # Check type
    assert isinstance(result, FeatureExtractionResult)

    # Check attributes
    assert result.embeddings.shape[0] > 0  # At least some patches
    assert result.embeddings.shape[1] == 512  # Embedding dim from config
    assert result.num_patches == result.embeddings.shape[0]
    assert result.embedding_dim == 512
    assert len(result.coordinates) == result.num_patches
    assert result.slide_id == "test_slide"
    assert result.model_id == "test_model"


def test_extract_features_custom_tile_size(loaded_mock_provider):
    """Test extraction avec tile_size custom."""
    result = loaded_mock_provider.extract_features("test_slide.mrxs", tile_size=256, overlap=32)

    assert result.tile_size == 256
    assert result.metadata["overlap"] == 32


def test_extract_features_not_loaded(mock_provider):
    """Test erreur si extract_features appelé sans modèle chargé."""
    with pytest.raises(MLModelNotLoadedError):
        mock_provider.extract_features("test_slide.mrxs")


# ============================================================================
# TEST HEATMAP GENERATION
# ============================================================================


def test_generate_heatmap_basic(loaded_mock_provider):
    """Test génération heatmap basique."""
    result = loaded_mock_provider.generate_heatmap("test_slide.mrxs", "malignant")

    # Check type
    assert isinstance(result, HeatmapResult)

    # Check attributes
    assert result.heatmap.ndim == 2  # 2D heatmap
    assert result.heatmap.shape[0] > 0
    assert result.heatmap.shape[1] > 0
    assert result.heatmap.min() >= 0.0
    assert result.heatmap.max() <= 1.0
    assert result.slide_id == "test_slide"
    assert result.method == "mock_gradcam"
    assert result.target_class == "malignant"


def test_generate_heatmap_resolution_levels(loaded_mock_provider):
    """Test génération heatmap à différentes résolutions."""
    result_level0 = loaded_mock_provider.generate_heatmap(
        "test_slide.mrxs", "malignant", resolution_level=0
    )
    result_level2 = loaded_mock_provider.generate_heatmap(
        "test_slide.mrxs", "malignant", resolution_level=2
    )

    # Level 0 devrait être plus grand que level 2
    assert result_level0.heatmap.size > result_level2.heatmap.size
    assert result_level0.resolution_level == 0
    assert result_level2.resolution_level == 2


def test_heatmap_to_rgb(loaded_mock_provider):
    """Test conversion heatmap vers RGB."""
    result = loaded_mock_provider.generate_heatmap("test_slide.mrxs", "malignant")
    rgb = result.to_rgb(colormap="jet")

    # Check RGB shape
    assert rgb.ndim == 3
    assert rgb.shape[2] == 3  # RGB channels
    assert rgb.dtype == np.uint8
    assert rgb.min() >= 0
    assert rgb.max() <= 255


def test_generate_heatmap_not_loaded(mock_provider):
    """Test erreur si generate_heatmap appelé sans modèle chargé."""
    with pytest.raises(MLModelNotLoadedError):
        mock_provider.generate_heatmap("test_slide.mrxs", "malignant")


# ============================================================================
# TEST DATA CLASSES VALIDATION
# ============================================================================


def test_prediction_result_validation():
    """Test validation PredictionResult."""
    # Valid
    result = PredictionResult(
        prediction_class="tumor",
        confidence=0.9,
        probabilities={"tumor": 0.9, "normal": 0.1},
        uncertainty=0.05,
    )
    assert result.confidence == 0.9

    # Invalid confidence (> 1.0)
    with pytest.raises(ValueError, match="Confidence must be in"):
        PredictionResult(prediction_class="tumor", confidence=1.5, probabilities={"tumor": 1.0})

    # Invalid probabilities (don't sum to 1)
    with pytest.raises(ValueError, match=r"Probabilities must sum to 1\.0"):
        PredictionResult(
            prediction_class="tumor", confidence=0.9, probabilities={"tumor": 0.5, "normal": 0.3}
        )


def test_feature_extraction_result_validation():
    """Test validation FeatureExtractionResult."""
    embeddings = np.random.randn(100, 512)
    coordinates = [(i * 224, 0) for i in range(100)]

    # Valid
    result = FeatureExtractionResult(embeddings=embeddings, coordinates=coordinates)
    assert result.num_patches == 100
    assert result.embedding_dim == 512

    # Invalid: coordinates length mismatch
    with pytest.raises(ValueError, match="Coordinates length"):
        FeatureExtractionResult(embeddings=embeddings, coordinates=coordinates[:50])

    # Invalid: embeddings not 2D
    with pytest.raises(ValueError, match="Embeddings must be 2D"):
        FeatureExtractionResult(embeddings=np.random.randn(100), coordinates=coordinates)


def test_heatmap_result_validation():
    """Test validation HeatmapResult."""
    heatmap = np.random.rand(256, 256)  # Normalized [0, 1]

    # Valid
    result = HeatmapResult(heatmap=heatmap, slide_dimensions=(10000, 10000), resolution_level=2)
    assert result.heatmap.shape == (256, 256)

    # Invalid: heatmap not 2D
    with pytest.raises(ValueError, match="Heatmap must be 2D"):
        HeatmapResult(
            heatmap=np.random.rand(256, 256, 3),
            slide_dimensions=(10000, 10000),
            resolution_level=2,
        )

    # Invalid: values not normalized
    with pytest.raises(ValueError, match="Heatmap values must be normalized"):
        HeatmapResult(
            heatmap=np.random.rand(256, 256) * 2.0,  # Values > 1.0
            slide_dimensions=(10000, 10000),
            resolution_level=2,
        )


# ============================================================================
# TEST WORKFLOW COMPLET
# ============================================================================


def test_complete_ml_workflow(mock_provider):
    """Test workflow ML complet."""
    # 1. Load model
    config = {
        "model_id": "workflow_test",
        "classes": ["benign", "malignant"],
        "embedding_dim": 256,
    }
    mock_provider.load_model("mock://workflow_test", config)

    # 2. Predict
    pred_result = mock_provider.predict("test_slide.mrxs")
    assert pred_result.prediction_class in ["benign", "malignant"]

    # 3. Extract features
    feature_result = mock_provider.extract_features("test_slide.mrxs", tile_size=224)
    assert feature_result.num_patches > 0

    # 4. Generate heatmap
    heatmap_result = mock_provider.generate_heatmap("test_slide.mrxs", pred_result.prediction_class)
    assert heatmap_result.heatmap.size > 0

    # 5. Get model info
    info = mock_provider.get_model_info()
    assert info["model_id"] == "workflow_test"

    # 6. Unload
    mock_provider.unload_model()
    assert not mock_provider.model_loaded


# ============================================================================
# MARKS
# ============================================================================


pytestmark = pytest.mark.unit
