"""Tests for disk cache service (embeddings .npy storage)"""

import numpy as np
import pytest


@pytest.mark.unit
class TestDiskCache:
    def test_save_and_load_embeddings(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        slide_id = "test_slide_001"
        model = "phikon_v1"
        embeddings = np.random.rand(100, 1024).astype(np.float32)

        cache.save_embeddings(slide_id, model, embeddings)
        loaded = cache.load_embeddings(slide_id, model)

        assert loaded is not None
        assert loaded.shape == (100, 1024)
        np.testing.assert_array_almost_equal(loaded, embeddings)

    def test_load_missing_returns_none(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        result = cache.load_embeddings("nonexistent", "model")
        assert result is None

    def test_invalidate(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        embeddings = np.random.rand(10, 1024).astype(np.float32)
        cache.save_embeddings("slide1", "model1", embeddings)

        cache.invalidate("slide1", "model1")
        assert cache.load_embeddings("slide1", "model1") is None

    def test_exists(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        embeddings = np.random.rand(5, 1024).astype(np.float32)

        assert not cache.exists("slide1", "model1")
        cache.save_embeddings("slide1", "model1", embeddings)
        assert cache.exists("slide1", "model1")

    def test_save_and_load_heatmap(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        heatmap = np.random.rand(256, 256).astype(np.float32)

        cache.save_heatmap("slide1", "model1", heatmap)
        loaded = cache.load_heatmap("slide1", "model1")

        assert loaded is not None
        np.testing.assert_array_almost_equal(loaded, heatmap)
