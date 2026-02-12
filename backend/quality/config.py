"""
Quality Metrics Configuration - Thresholds and defaults.
"""

# IoU matching threshold for considering two annotations as "matched"
DEFAULT_IOU_THRESHOLD = 0.5

# Grid cell size in pixels for grid-based matching
DEFAULT_GRID_CELL_SIZE = 256

# Buffer radius in pixels for point annotations (ST_Buffer)
DEFAULT_POINT_BUFFER_RADIUS = 50.0

# Cache TTL for quality reports (seconds)
CACHE_TTL_SECONDS = 300  # 5 minutes

# Label assigned to annotations without a label
UNLABELED_CATEGORY = "Unlabeled"
