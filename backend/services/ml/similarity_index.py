"""
FAISS Vector Index for Slide Similarity Search

Stores mean-pooled slide embeddings (one vector per slide).
Uses cosine similarity via inner product on L2-normalized vectors.

Index files:
    {index_dir}/faiss_slide_index.bin  -- FAISS IndexFlatIP
    {index_dir}/faiss_slide_ids.json   -- ordered list of slide IDs
"""

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Optional FAISS import (graceful degradation)
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("faiss-cpu not installed — similarity search disabled")


class SimilarityIndex:
    """FAISS-based vector index for slide similarity search.

    Stores mean-pooled slide embeddings (one vector per slide).
    Uses cosine similarity via inner product on L2-normalized vectors.

    Index files:
        {index_dir}/faiss_slide_index.bin  -- FAISS IndexFlatIP
        {index_dir}/faiss_slide_ids.json   -- ordered list of slide IDs
    """

    def __init__(self, index_dir: str = "/tmp/varuna_cache/ml/index"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index = None  # faiss.IndexFlatIP
        self.slide_ids: list[str] = []  # same order as index
        self._load_or_create()

    def _load_or_create(self):
        """Load existing index from disk, or create empty one."""
        index_path = self.index_dir / "faiss_slide_index.bin"
        ids_path = self.index_dir / "faiss_slide_ids.json"

        if index_path.exists() and ids_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(ids_path) as f:
                self.slide_ids = json.load(f)
            logger.info("Loaded FAISS index with %d slides", self.index.ntotal)
        else:
            # Will be initialized on first add (need to know embedding dim)
            self.index = None
            self.slide_ids = []

    def add_slide(self, slide_id: str, embeddings: np.ndarray):
        """Add a slide to the index.

        Args:
            slide_id: Unique slide identifier.
            embeddings: Shape (N, D) patch-level embeddings.
                       Mean-pooled to single (1, D) vector.
        """
        if slide_id in self.slide_ids:
            return  # Already indexed

        # Mean-pool patch embeddings to slide-level vector
        slide_vector = embeddings.mean(axis=0, keepdims=True).astype(np.float32)
        # L2-normalize for cosine similarity via inner product
        faiss.normalize_L2(slide_vector)

        if self.index is None:
            dim = slide_vector.shape[1]
            self.index = faiss.IndexFlatIP(dim)

        self.index.add(slide_vector)
        self.slide_ids.append(slide_id)

    def search(
        self,
        query_embeddings: np.ndarray,
        top_k: int = 5,
        exclude_id: str = None,
    ) -> list[dict]:
        """Search for similar slides.

        Args:
            query_embeddings: Shape (N, D) patch-level, or (1, D) slide-level.
            top_k: Number of results to return.
            exclude_id: Slide ID to exclude (the query slide itself).

        Returns:
            List of {slide_id: str, score: float} sorted by descending score.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        # Mean-pool if multi-patch
        if query_embeddings.ndim == 2 and query_embeddings.shape[0] > 1:
            query = query_embeddings.mean(axis=0, keepdims=True).astype(np.float32)
        else:
            query = query_embeddings.reshape(1, -1).astype(np.float32)

        faiss.normalize_L2(query)

        # Search more than needed in case we exclude one
        k = min(top_k + 1, self.index.ntotal)
        scores, indices = self.index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0], strict=False):
            if idx < 0 or idx >= len(self.slide_ids):
                continue
            sid = self.slide_ids[idx]
            if sid == exclude_id:
                continue
            results.append({"slide_id": sid, "score": float(score)})
            if len(results) >= top_k:
                break

        return results

    def save(self):
        """Persist index to disk."""
        if self.index is None:
            return
        faiss.write_index(self.index, str(self.index_dir / "faiss_slide_index.bin"))
        with open(self.index_dir / "faiss_slide_ids.json", "w") as f:
            json.dump(self.slide_ids, f)

    def size(self) -> int:
        """Number of indexed slides."""
        return self.index.ntotal if self.index else 0

    @property
    def is_available(self) -> bool:
        """Check if faiss is importable."""
        return FAISS_AVAILABLE
