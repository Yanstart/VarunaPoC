"""
Disk Cache Service -- Level 2 Cache

Stores computed numpy arrays (embeddings, heatmaps, detections) on disk
using .npy format. Organized by slide_id and model name.

Directory structure:
    {base_dir}/{slide_id}/{model}/{type}.npy

Thread-safe: uses atomic write (write to tmp, then rename).
"""

import logging
import os
import tempfile
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class DiskCache:
    """Numpy-based disk cache for ML computed results."""

    def __init__(self, base_dir: str = "/tmp/varuna_cache"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, slide_id: str, model: str, data_type: str = "embeddings") -> Path:
        """Build cache file path."""
        safe_id = slide_id.replace("/", "_").replace("\\", "_")
        return self.base_dir / safe_id / model / f"{data_type}.npy"

    def save_embeddings(self, slide_id: str, model: str, data: np.ndarray) -> None:
        """Save embeddings array to disk."""
        self._save(slide_id, model, "embeddings", data)

    def load_embeddings(self, slide_id: str, model: str) -> np.ndarray | None:
        """Load embeddings from disk. Returns None if not cached."""
        return self._load(slide_id, model, "embeddings")

    def save_heatmap(self, slide_id: str, model: str, data: np.ndarray) -> None:
        """Save heatmap array to disk."""
        self._save(slide_id, model, "heatmap", data)

    def load_heatmap(self, slide_id: str, model: str) -> np.ndarray | None:
        """Load heatmap from disk. Returns None if not cached."""
        return self._load(slide_id, model, "heatmap")

    def exists(self, slide_id: str, model: str, data_type: str = "embeddings") -> bool:
        """Check if cache entry exists."""
        return self._path(slide_id, model, data_type).exists()

    def invalidate(self, slide_id: str, model: str, data_type: str = "embeddings") -> None:
        """Remove a specific cache entry."""
        path = self._path(slide_id, model, data_type)
        if path.exists():
            path.unlink()
            logger.info("Cache invalidated: %s/%s/%s", slide_id, model, data_type)

    def _save(self, slide_id: str, model: str, data_type: str, data: np.ndarray) -> None:
        """Atomic save: write to temp file, then rename."""
        path = self._path(slide_id, model, data_type)
        path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(suffix=".npy", dir=str(path.parent))
        try:
            np.save(tmp_path, data)
            os.replace(tmp_path, str(path))
            logger.debug("Cached %s: %s (%s)", data_type, path, data.shape)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    def _load(self, slide_id: str, model: str, data_type: str) -> np.ndarray | None:
        """Load numpy array from disk."""
        path = self._path(slide_id, model, data_type)
        if not path.exists():
            return None
        try:
            return np.load(str(path))
        except Exception as e:
            logger.warning("Failed to load cache %s: %s", path, e)
            return None
