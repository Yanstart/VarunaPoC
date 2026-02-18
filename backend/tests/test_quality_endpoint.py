"""
Tests for Quality Control Service

Tests the QualityService mock mode and verifies
response shape matches issue #93 spec.

Markers: @pytest.mark.quality, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from services.ml.quality import ARTIFACT_TYPES, SEVERITY_LEVELS, QualityResult, QualityService


@pytest.mark.quality
@pytest.mark.unit
class TestQualityService:
    """Test QualityService in mock mode."""

    def setup_method(self):
        self.service = QualityService()

    def test_returns_quality_result(self):
        result = self.service.assess_quality("/slides/test_slide.svs")
        assert isinstance(result, QualityResult)

    def test_score_between_0_and_1(self):
        result = self.service.assess_quality("/slides/test_slide.svs")
        assert 0.0 <= result.overall_score <= 1.0

    def test_quality_label_matches_score_range_good(self):
        """Verify label 'Bonne' for scores > 0.8."""
        # Test multiple paths to find one with score > 0.8
        for i in range(50):
            result = self.service.assess_quality(f"/slides/slide_{i}.svs")
            if result.overall_score > 0.8:
                assert result.quality_label == "Bonne"
                return
        # At least verify label-score consistency for whatever we got
        result = self.service.assess_quality("/slides/test_slide.svs")
        if result.overall_score > 0.8:
            assert result.quality_label == "Bonne"
        elif result.overall_score >= 0.6:
            assert result.quality_label == "Acceptable"
        else:
            assert result.quality_label == "À refaire"

    def test_quality_label_matches_score_range_acceptable(self):
        """Verify label 'Acceptable' for scores 0.6-0.8."""
        for i in range(50):
            result = self.service.assess_quality(f"/slides/slide_{i}.svs")
            if 0.6 <= result.overall_score <= 0.8:
                assert result.quality_label == "Acceptable"
                return
        # Fallback: verify consistency
        result = self.service.assess_quality("/slides/test_slide.svs")
        self._assert_label_matches_score(result)

    def test_quality_label_matches_score_range_poor(self):
        """Verify label 'À refaire' for scores < 0.6."""
        for i in range(50):
            result = self.service.assess_quality(f"/slides/slide_{i}.svs")
            if result.overall_score < 0.6:
                assert result.quality_label == "À refaire"
                return
        # Fallback: verify consistency
        result = self.service.assess_quality("/slides/test_slide.svs")
        self._assert_label_matches_score(result)

    def _assert_label_matches_score(self, result):
        if result.overall_score > 0.8:
            assert result.quality_label == "Bonne"
        elif result.overall_score >= 0.6:
            assert result.quality_label == "Acceptable"
        else:
            assert result.quality_label == "À refaire"

    def test_artifacts_have_valid_types(self):
        """All artifact types must be one of the known types."""
        # Test multiple slides to find one with artifacts
        for i in range(20):
            result = self.service.assess_quality(f"/slides/slide_{i}.svs")
            for artifact in result.artifacts:
                assert artifact.type in ARTIFACT_TYPES, f"Unknown artifact type: {artifact.type}"

    def test_artifacts_have_valid_severity(self):
        """All artifact severities must be valid."""
        for i in range(20):
            result = self.service.assess_quality(f"/slides/slide_{i}.svs")
            for artifact in result.artifacts:
                assert (
                    artifact.severity in SEVERITY_LEVELS
                ), f"Unknown severity: {artifact.severity}"

    def test_artifacts_have_valid_bbox(self):
        """Artifact bbox must be [x1, y1, x2, y2] with valid coords."""
        for i in range(20):
            result = self.service.assess_quality(f"/slides/slide_{i}.svs")
            for artifact in result.artifacts:
                assert len(artifact.bbox) == 4
                x1, y1, x2, y2 = artifact.bbox
                assert x2 > x1
                assert y2 > y1

    def test_deterministic_for_same_path(self):
        """Same slide path should always produce same quality result."""
        r1 = self.service.assess_quality("/slides/test_slide.svs")
        r2 = self.service.assess_quality("/slides/test_slide.svs")
        assert r1.overall_score == r2.overall_score
        assert r1.quality_label == r2.quality_label
        assert len(r1.artifacts) == len(r2.artifacts)

    def test_processing_time_non_negative(self):
        result = self.service.assess_quality("/slides/test_slide.svs")
        assert result.processing_time_ms >= 0

    def test_recommendation_is_non_empty_string(self):
        result = self.service.assess_quality("/slides/test_slide.svs")
        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0

    def test_metadata_mode_mock(self):
        result = self.service.assess_quality("/slides/test_slide.svs")
        assert result.metadata.get("mode") == "mock"

    def test_artifacts_count_in_range(self):
        """Mock mode produces 0-3 artifacts."""
        result = self.service.assess_quality("/slides/test_slide.svs")
        assert 0 <= len(result.artifacts) <= 3
