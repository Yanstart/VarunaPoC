"""
Clustering Service — Morphological clustering of slide embeddings.

Two modes:
- Mock mode (default): Deterministic 8x8 grid seeded from slide path hash.
- Real mode: Loads embeddings from DiskCache, runs sklearn KMeans, returns assignments.

Reference: Clustering plan Tasks 1-2
"""

import hashlib
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

CLUSTER_COLORS = [
    "#e74c3c",
    "#2ecc71",
    "#3498db",
    "#f39c12",
    "#9b59b6",
    "#1abc9c",
    "#e67e22",
    "#34495e",
]


@dataclass
class ClusterInfo:
    id: int
    color: str
    label: str
    tile_count: int
    centroid_embedding: List[float] = field(default_factory=list)


@dataclass
class TileAssignment:
    x: int
    y: int
    cluster_id: int


@dataclass
class ClusterResult:
    clusters: List[ClusterInfo]
    tile_assignments: List[TileAssignment]
    processing_time_ms: float
    metadata: Optional[Dict] = field(default_factory=dict)


class ClusteringService:
    """Clustering service with mock and real modes."""

    def cluster(
        self,
        slide_path: str,
        n_clusters: int = 4,
        disk_cache=None,
        model_id: str = "unknown",
    ) -> ClusterResult:
        """
        Cluster tiles in a slide.

        If disk_cache has cached embeddings and sklearn is available,
        uses real KMeans clustering. Otherwise falls back to
        deterministic mock mode.
        """
        start = time.time()

        # Cap n_clusters at number of available colors
        n_clusters = min(n_clusters, len(CLUSTER_COLORS))

        # Try real mode if disk_cache is available
        if disk_cache is not None:
            try:
                result = self._cluster_real(slide_path, n_clusters, disk_cache, model_id)
                result.processing_time_ms = (time.time() - start) * 1000
                return result
            except Exception as e:
                logger.warning("Real clustering failed, falling back to mock: %s", e)

        # Mock mode
        result = self._cluster_mock(slide_path, n_clusters, model_id)
        result.processing_time_ms = (time.time() - start) * 1000
        return result

    def _cluster_mock(
        self, slide_path: str, n_clusters: int, model_id: str = "unknown"
    ) -> ClusterResult:
        """Deterministic mock clustering seeded from slide path hash."""
        seed = int(hashlib.md5(slide_path.encode()).hexdigest(), 16) % (2**32)
        import random

        rng = random.Random(seed)

        # 8x8 grid of tile assignments
        grid_size = 8
        tile_assignments = []
        tile_counts = [0] * n_clusters

        for y in range(grid_size):
            for x in range(grid_size):
                cluster_id = rng.randint(0, n_clusters - 1)
                tile_assignments.append(TileAssignment(x=x, y=y, cluster_id=cluster_id))
                tile_counts[cluster_id] += 1

        # Build cluster info
        clusters = []
        for i in range(n_clusters):
            label_char = chr(ord("A") + i)
            clusters.append(
                ClusterInfo(
                    id=i,
                    color=CLUSTER_COLORS[i],
                    label=f"Cluster {label_char}",
                    tile_count=tile_counts[i],
                    centroid_embedding=[],
                )
            )

        return ClusterResult(
            clusters=clusters,
            tile_assignments=tile_assignments,
            processing_time_ms=0,
            metadata={"mode": "mock", "grid_size": grid_size, "model_id": model_id},
        )

    def _cluster_real(
        self,
        slide_path: str,
        n_clusters: int,
        disk_cache,
        model_id: str,
    ) -> ClusterResult:
        """Real clustering via KMeans on cached embeddings."""
        # Extract slide_id from path for cache lookup
        from pathlib import Path

        import numpy as np
        from sklearn.cluster import KMeans

        slide_id = Path(slide_path).stem

        # Load embeddings from disk cache
        embeddings = disk_cache.load_embeddings(slide_id, model_id)
        if embeddings is None:
            raise ValueError(f"No cached embeddings for slide {slide_id} / model {model_id}")

        n_tiles = embeddings.shape[0]
        n_clusters = min(n_clusters, n_tiles)

        # Run KMeans
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        # Build square-ish grid layout
        grid_w = math.ceil(math.sqrt(n_tiles))

        tile_assignments = []
        tile_counts = [0] * n_clusters
        for idx in range(n_tiles):
            x = idx % grid_w
            y = idx // grid_w
            cluster_id = int(labels[idx])
            tile_assignments.append(TileAssignment(x=x, y=y, cluster_id=cluster_id))
            tile_counts[cluster_id] += 1

        # Build cluster info with centroids
        clusters = []
        for i in range(n_clusters):
            label_char = chr(ord("A") + i)
            centroid = kmeans.cluster_centers_[i].tolist()
            clusters.append(
                ClusterInfo(
                    id=i,
                    color=CLUSTER_COLORS[i],
                    label=f"Cluster {label_char}",
                    tile_count=tile_counts[i],
                    centroid_embedding=centroid,
                )
            )

        return ClusterResult(
            clusters=clusters,
            tile_assignments=tile_assignments,
            processing_time_ms=0,
            metadata={
                "mode": "real",
                "model_id": model_id,
                "n_tiles": n_tiles,
                "grid_w": grid_w,
            },
        )
