"""Tests for background embedding pre-computation."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


class TestPrecomputeEmbeddings:
    @pytest.mark.asyncio
    async def test_skips_if_cached(self):
        """Should skip extraction if embeddings are already cached."""
        from services.background_tasks import precompute_embeddings, _active_tasks
        _active_tasks.discard("test-slide")  # Clean state

        with patch("services.background_tasks.DiskCache") as MockCache:
            mock_cache = MockCache.return_value
            mock_cache.exists.return_value = True

            await precompute_embeddings("test-slide", "/fake/path.svs")
            mock_cache.exists.assert_called_once()
            mock_cache.save_embeddings.assert_not_called()

    @pytest.mark.asyncio
    async def test_saves_to_cache(self):
        """Should extract and save embeddings when not cached."""
        import numpy as np
        from services.background_tasks import precompute_embeddings, _active_tasks
        _active_tasks.discard("test-slide-2")

        mock_result = MagicMock()
        mock_result.embeddings = np.zeros((10, 512))

        with patch("services.background_tasks.DiskCache") as MockCache,              patch("services.background_tasks.get_provider") as mock_get_provider:
            mock_cache = MockCache.return_value
            mock_cache.exists.return_value = False

            mock_provider = MagicMock()
            mock_provider.model_loaded = True
            mock_provider.extract_features.return_value = mock_result
            mock_get_provider.return_value = mock_provider

            await precompute_embeddings("test-slide-2", "/fake/path.svs")
            mock_cache.save_embeddings.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_error(self):
        """Should not crash on provider error."""
        from services.background_tasks import precompute_embeddings, _active_tasks
        _active_tasks.discard("test-slide-3")

        with patch("services.background_tasks.DiskCache") as MockCache,              patch("services.background_tasks.get_provider") as mock_get_provider:
            mock_cache = MockCache.return_value
            mock_cache.exists.return_value = False

            mock_provider = MagicMock()
            mock_provider.model_loaded = True
            mock_provider.extract_features.side_effect = RuntimeError("GPU OOM")
            mock_get_provider.return_value = mock_provider

            # Should not raise
            await precompute_embeddings("test-slide-3", "/fake/path.svs")

    @pytest.mark.asyncio
    async def test_deduplicates(self):
        """Should skip if task already in progress."""
        from services.background_tasks import precompute_embeddings, _active_tasks
        _active_tasks.add("test-slide-4")  # Simulate in-progress

        with patch("services.background_tasks.DiskCache") as MockCache:
            await precompute_embeddings("test-slide-4", "/fake/path.svs")
            MockCache.assert_not_called()

        _active_tasks.discard("test-slide-4")
