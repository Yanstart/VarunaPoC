"""
Tests for Retraining Pipeline Service and Endpoint

Tests the RetrainingPipelineService mock mode and verifies
response shape matches issue #97 spec.

Markers: @pytest.mark.retraining, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from services.ml.retraining import RetrainingPipelineService, RetrainingResult


@pytest.mark.retraining
@pytest.mark.unit
class TestRetrainingPipelineService:
    """Test RetrainingPipelineService in mock mode."""

    def setup_method(self):
        self.service = RetrainingPipelineService()

    @pytest.mark.asyncio
    async def test_trigger_returns_retraining_result(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert isinstance(result, RetrainingResult)

    @pytest.mark.asyncio
    async def test_response_has_run_id(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert isinstance(result.run_id, str)
        assert len(result.run_id) > 0

    @pytest.mark.asyncio
    async def test_response_has_status_completed(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_response_has_model_name(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert result.model_name == "ctranspath"

    @pytest.mark.asyncio
    async def test_response_has_dataset_version(self):
        result = await self.service.trigger_retraining("ctranspath", "v2.0")
        assert result.dataset_version == "v2.0"

    @pytest.mark.asyncio
    async def test_metrics_contain_accuracy(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert "accuracy" in result.metrics
        assert 0.0 <= result.metrics["accuracy"] <= 1.0

    @pytest.mark.asyncio
    async def test_metrics_contain_auc_roc(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert "auc_roc" in result.metrics
        assert 0.0 <= result.metrics["auc_roc"] <= 1.0

    @pytest.mark.asyncio
    async def test_metrics_contain_f1_score(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert "f1_score" in result.metrics
        assert 0.0 <= result.metrics["f1_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_recommendation_is_non_empty_string(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0

    @pytest.mark.asyncio
    async def test_processing_time_is_non_negative(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert result.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_artifact_uri_is_s3_path(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert result.artifact_uri is not None
        assert result.artifact_uri.startswith("s3://")

    @pytest.mark.asyncio
    async def test_deterministic_for_same_inputs(self):
        """Same model_id and dataset_tag should produce same results."""
        r1 = await self.service.trigger_retraining("ctranspath", "v1.0")
        r2 = await self.service.trigger_retraining("ctranspath", "v1.0")
        assert r1.run_id == r2.run_id
        assert r1.metrics["accuracy"] == r2.metrics["accuracy"]
        assert r1.metrics["auc_roc"] == r2.metrics["auc_roc"]
        assert r1.metrics["f1_score"] == r2.metrics["f1_score"]

    @pytest.mark.asyncio
    async def test_different_model_ids_produce_different_results(self):
        """Different model_ids should produce different metric values."""
        r1 = await self.service.trigger_retraining("ctranspath")
        r2 = await self.service.trigger_retraining("phikon-v2")
        assert r1.metrics["accuracy"] != r2.metrics["accuracy"]

    @pytest.mark.asyncio
    async def test_different_dataset_tags_produce_different_results(self):
        """Different dataset_tags should produce different metric values."""
        r1 = await self.service.trigger_retraining("ctranspath", "v1.0")
        r2 = await self.service.trigger_retraining("ctranspath", "v2.0")
        assert r1.metrics["accuracy"] != r2.metrics["accuracy"]

    @pytest.mark.asyncio
    async def test_default_dataset_tag_is_latest(self):
        result = await self.service.trigger_retraining("ctranspath")
        assert result.dataset_version == "latest"

    @pytest.mark.asyncio
    async def test_pipeline_status(self):
        status = await self.service.get_pipeline_status("mock-run-abc123")
        assert status["run_id"] == "mock-run-abc123"
        assert status["status"] == "completed"
        assert status["progress"] == 100
