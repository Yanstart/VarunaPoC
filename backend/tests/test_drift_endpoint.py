"""
Tests for Drift Detector Service

Tests the DriftDetectorService mock mode and verifies
response shape matches issue #95 spec.

Markers: @pytest.mark.drift, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from services.ml.drift import DriftDetectorService, ModelDriftReport


@pytest.mark.drift
@pytest.mark.unit
class TestDriftDetectorService:
    """Test DriftDetectorService in mock mode."""

    def setup_method(self):
        self.service = DriftDetectorService()

    def test_returns_model_drift_report(self):
        result = self.service.detect_drift("ctranspath")
        assert isinstance(result, ModelDriftReport)

    def test_metrics_include_mmd_and_ks(self):
        result = self.service.detect_drift("ctranspath")
        metric_names = {m.metric_name for m in result.metrics}
        assert "mmd" in metric_names
        assert "ks_statistic" in metric_names

    def test_threshold_values_are_positive(self):
        result = self.service.detect_drift("ctranspath")
        for m in result.metrics:
            assert m.threshold > 0

    def test_is_drifted_matches_threshold_comparison(self):
        result = self.service.detect_drift("ctranspath")
        for m in result.metrics:
            expected = m.value > m.threshold
            assert m.is_drifted == expected, (
                f"Metric {m.metric_name}: value={m.value}, "
                f"threshold={m.threshold}, is_drifted={m.is_drifted}"
            )

    def test_deterministic_for_same_model_id(self):
        """Same model_id should always produce same metrics."""
        r1 = self.service.detect_drift("ctranspath")
        r2 = self.service.detect_drift("ctranspath")
        for m1, m2 in zip(r1.metrics, r2.metrics, strict=True):
            assert m1.value == m2.value
            assert m1.is_drifted == m2.is_drifted

    def test_recommendation_non_empty(self):
        result = self.service.detect_drift("ctranspath")
        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0

    def test_processing_time_non_negative(self):
        result = self.service.detect_drift("ctranspath")
        assert result.processing_time_ms >= 0

    def test_overall_drifted_true_when_any_metric_exceeds(self):
        """overall_drifted should be True if any metric exceeds threshold."""
        result = self.service.detect_drift("ctranspath")
        any_drifted = any(m.is_drifted for m in result.metrics)
        assert result.overall_drifted == any_drifted

    def test_recommendation_matches_drift_status(self):
        result = self.service.detect_drift("ctranspath")
        if result.overall_drifted:
            assert result.recommendation == "Consider retraining"
        else:
            assert result.recommendation == "No action needed"

    def test_different_models_may_differ(self):
        """Different model_ids should produce different metric values."""
        r1 = self.service.detect_drift("ctranspath")
        r2 = self.service.detect_drift("phikon-v2")
        vals1 = [m.value for m in r1.metrics]
        vals2 = [m.value for m in r2.metrics]
        assert vals1 != vals2

    def test_report_date_is_iso_format(self):
        result = self.service.detect_drift("ctranspath")
        assert isinstance(result.report_date, str)
        # Should be parseable as ISO datetime
        from datetime import datetime

        datetime.fromisoformat(result.report_date)

    def test_metadata_mode_mock(self):
        result = self.service.detect_drift("ctranspath")
        assert result.metadata.get("mode") == "mock"

    def test_window_size_positive(self):
        result = self.service.detect_drift("ctranspath")
        for m in result.metrics:
            assert m.window_size > 0

    def test_mmd_value_in_expected_range(self):
        result = self.service.detect_drift("ctranspath")
        mmd = next(m for m in result.metrics if m.metric_name == "mmd")
        assert 0.01 <= mmd.value <= 0.15

    def test_ks_value_in_expected_range(self):
        result = self.service.detect_drift("ctranspath")
        ks = next(m for m in result.metrics if m.metric_name == "ks_statistic")
        assert 0.05 <= ks.value <= 0.25
