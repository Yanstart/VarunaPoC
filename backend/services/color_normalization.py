"""
Color Normalization Service — Stain normalization for histopathology images.

Implements Reinhard and Macenko stain normalization methods for
standardizing H&E stained tissue images across different scanners
and staining protocols.

Methods:
- Reinhard: Mean/std transfer in LAB color space (simple, fast).
- Macenko: SVD-based stain vector decomposition (more accurate).
- Vahadane: Falls back to Macenko (simplified).

Reference: Issue #11
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Default reference stain matrix for H&E (Macenko)
# Rows: Hematoxylin, Eosin; Columns: R, G, B in OD space
HE_REF_STAIN_MATRIX = np.array(
    [
        [0.5626, 0.7201, 0.4062],  # Hematoxylin
        [0.2159, 0.8012, 0.5581],  # Eosin
    ]
)

# Default reference statistics for Reinhard normalization (LAB space)
# Computed from a canonical H&E reference image
REINHARD_REF_STATS = {
    "mean": np.array([70.0, 15.0, -10.0], dtype=np.float64),
    "std": np.array([15.0, 10.0, 8.0], dtype=np.float64),
}


@dataclass
class NormalizationResult:
    """Metadata about a completed normalization."""

    method: str
    processing_time_ms: float
    tile_count: int
    reference_stain: str


class ColorNormalizationService:
    """Stain normalization for histopathology images."""

    METHODS = ("macenko", "reinhard", "vahadane")

    def normalize_tile(
        self,
        tile: np.ndarray,
        method: str = "macenko",
        reference: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Normalize a single tile's stain colors.

        Args:
            tile: Input image as numpy array (H, W, 3), uint8 RGB.
            method: Normalization method ("reinhard", "macenko", or "vahadane").
            reference: Optional reference image for computing target statistics.
                       If None, default reference statistics are used.

        Returns:
            Normalized image as numpy array (H, W, 3), uint8 RGB.

        Raises:
            ValueError: If method is unknown.
        """
        if method == "reinhard":
            return self._reinhard_normalize(tile, reference)
        elif method == "macenko":
            return self._macenko_normalize(tile, reference)
        elif method == "vahadane":
            # Vahadane uses sparse NMF which is complex; fall back to Macenko
            return self._macenko_normalize(tile, reference)
        raise ValueError(f"Unknown method: {method}")

    def normalize_batch(
        self,
        tiles: List[np.ndarray],
        method: str = "macenko",
        reference: Optional[np.ndarray] = None,
    ) -> Tuple[List[np.ndarray], NormalizationResult]:
        """
        Normalize a batch of tiles.

        Args:
            tiles: List of input images (H, W, 3), uint8 RGB.
            method: Normalization method.
            reference: Optional reference image.

        Returns:
            Tuple of (normalized tiles, NormalizationResult metadata).
        """
        start = time.time()

        normalized = []
        for tile in tiles:
            normalized.append(self.normalize_tile(tile, method, reference))

        elapsed_ms = (time.time() - start) * 1000

        result = NormalizationResult(
            method=method,
            processing_time_ms=round(elapsed_ms, 2),
            tile_count=len(tiles),
            reference_stain="default" if reference is None else "custom",
        )

        return normalized, result

    # ------------------------------------------------------------------
    # Reinhard normalization
    # ------------------------------------------------------------------

    def _reinhard_normalize(
        self,
        source: np.ndarray,
        reference: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Reinhard color normalization (mean/std transfer in LAB space).

        Algorithm:
        1. Convert source (and reference) from RGB to LAB.
        2. Compute mean and std for each LAB channel.
        3. Shift source to match reference statistics: out = (src - src_mean) * (ref_std / src_std) + ref_mean.
        4. Convert back to RGB.

        Reference: Reinhard et al., "Color Transfer between Images", 2001.
        """
        # Handle blank/white tiles gracefully
        if source.size == 0 or source.ndim != 3 or source.shape[2] != 3:
            return source.copy()

        # Convert to float
        source_f = source.astype(np.float64) / 255.0

        # RGB -> LAB (simplified conversion via XYZ)
        source_lab = self._rgb_to_lab(source_f)

        # Compute source statistics
        src_mean = np.mean(source_lab, axis=(0, 1))
        src_std = np.std(source_lab, axis=(0, 1))

        # Avoid division by zero for blank tiles
        src_std = np.where(src_std < 1e-6, 1.0, src_std)

        # Reference statistics
        if reference is not None:
            ref_f = reference.astype(np.float64) / 255.0
            ref_lab = self._rgb_to_lab(ref_f)
            ref_mean = np.mean(ref_lab, axis=(0, 1))
            ref_std = np.std(ref_lab, axis=(0, 1))
            ref_std = np.where(ref_std < 1e-6, 1.0, ref_std)
        else:
            ref_mean = REINHARD_REF_STATS["mean"]
            ref_std = REINHARD_REF_STATS["std"]

        # Apply mean/std transfer in LAB space
        result_lab = (source_lab - src_mean) * (ref_std / src_std) + ref_mean

        # Convert LAB back to RGB, clip and return as uint8
        result_rgb = self._lab_to_rgb(result_lab)
        return np.clip(result_rgb * 255.0, 0, 255).astype(np.uint8)

    # ------------------------------------------------------------------
    # Macenko normalization
    # ------------------------------------------------------------------

    def _macenko_normalize(
        self,
        source: np.ndarray,
        reference: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Macenko stain normalization via SVD.

        Algorithm:
        1. Convert to optical density (OD) space.
        2. Remove background (low OD) pixels.
        3. SVD to find principal stain directions.
        4. Project pixels onto stain vectors to get concentrations.
        5. Normalize concentrations to match reference.
        6. Reconstruct image.

        Reference: Macenko et al., "A method for normalizing histology slides
        for quantitative analysis", ISBI 2009.
        """
        # Handle blank/white tiles
        if source.size == 0 or source.ndim != 3 or source.shape[2] != 3:
            return source.copy()

        h, w, _ = source.shape
        source_f = source.reshape(-1, 3).astype(np.float64)

        # Step 1: Convert to OD space: OD = -log10(I/I0), I0=255
        source_od = self._rgb_to_od(source_f)

        # Step 2: Filter background (keep pixels with significant OD)
        od_threshold = 0.15
        od_mask = np.any(source_od > od_threshold, axis=1)

        if np.sum(od_mask) < 10:
            # Too few tissue pixels; return original
            return source.copy()

        tissue_od = source_od[od_mask]

        # Step 3: SVD to find stain vectors
        try:
            stain_matrix = self._get_stain_vectors(tissue_od)
        except Exception:
            # SVD failed; return original image
            logger.debug("Macenko SVD failed; returning original tile")
            return source.copy()

        # Project onto stain vectors to get stain concentrations
        stain_pinv = np.linalg.pinv(stain_matrix)
        concentrations = source_od @ stain_pinv

        # Reference stain matrix
        if reference is not None:
            ref_f = reference.reshape(-1, 3).astype(np.float64)
            ref_od = self._rgb_to_od(ref_f)
            ref_mask = np.any(ref_od > od_threshold, axis=1)
            if np.sum(ref_mask) >= 10:
                ref_tissue = ref_od[ref_mask]
                try:
                    ref_stain = self._get_stain_vectors(ref_tissue)
                except Exception:
                    ref_stain = HE_REF_STAIN_MATRIX
            else:
                ref_stain = HE_REF_STAIN_MATRIX
        else:
            ref_stain = HE_REF_STAIN_MATRIX

        # Step 5: Normalize concentrations
        # Scale each stain channel to match reference max
        src_max = np.percentile(concentrations, 99, axis=0)  # (2,)
        ref_pinv = np.linalg.pinv(ref_stain)  # (3, 2)
        ref_conc = source_od @ ref_pinv  # (N, 2)
        ref_max = np.percentile(ref_conc, 99, axis=0)  # (2,)

        # Avoid division by zero
        src_max = np.where(np.abs(src_max) < 1e-6, 1.0, src_max)
        scale = ref_max / src_max
        concentrations_normalized = concentrations * scale

        # Step 6: Reconstruct: OD = concentrations @ stain_matrix -> (N, 2) @ (2, 3) = (N, 3)
        reconstructed_od = concentrations_normalized @ ref_stain
        reconstructed_rgb = self._od_to_rgb(reconstructed_od)
        reconstructed_rgb = np.clip(reconstructed_rgb, 0, 255).astype(np.uint8)

        return reconstructed_rgb.reshape(h, w, 3)

    # ------------------------------------------------------------------
    # Color space conversions
    # ------------------------------------------------------------------

    @staticmethod
    def _rgb_to_od(rgb: np.ndarray) -> np.ndarray:
        """Convert RGB (0-255 scale) to Optical Density space."""
        rgb_clipped = np.clip(rgb, 1.0, 255.0)
        return -np.log10(rgb_clipped / 255.0)

    @staticmethod
    def _od_to_rgb(od: np.ndarray) -> np.ndarray:
        """Convert Optical Density back to RGB (0-255 scale)."""
        return 255.0 * np.power(10, -od)

    @staticmethod
    def _get_stain_vectors(tissue_od: np.ndarray) -> np.ndarray:
        """
        Extract 2 principal stain vectors from tissue OD data via SVD.

        Returns:
            (2, 3) array of stain vectors (Hematoxylin, Eosin).
        """
        # Center the data
        mean_od = np.mean(tissue_od, axis=0)
        centered = tissue_od - mean_od

        # SVD to extract right singular vectors
        _, _, vt = np.linalg.svd(centered, full_matrices=False)

        # Take the first two principal components
        plane = vt[:2, :]

        # Project tissue OD onto the plane
        projected = tissue_od @ plane.T

        # Find the angle of each projected point
        angles = np.arctan2(projected[:, 1], projected[:, 0])

        # Use percentile angles to identify the two stain extremes
        min_angle = np.percentile(angles, 1)
        max_angle = np.percentile(angles, 99)

        # Convert back to stain vectors
        stain1 = np.cos(min_angle) * plane[0] + np.sin(min_angle) * plane[1]
        stain2 = np.cos(max_angle) * plane[0] + np.sin(max_angle) * plane[1]

        # Ensure positive direction
        if stain1[0] < 0:
            stain1 = -stain1
        if stain2[0] < 0:
            stain2 = -stain2

        # Normalize to unit length
        stain1 = stain1 / (np.linalg.norm(stain1) + 1e-10)
        stain2 = stain2 / (np.linalg.norm(stain2) + 1e-10)

        return np.array([stain1, stain2])

    @staticmethod
    def _rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
        """
        Convert RGB (0-1 float) to CIE LAB color space.

        Uses simplified sRGB -> XYZ -> LAB pipeline.
        """
        # sRGB gamma correction
        mask = rgb > 0.04045
        rgb_linear = np.where(mask, np.power((rgb + 0.055) / 1.055, 2.4), rgb / 12.92)

        # RGB to XYZ (D65 illuminant)
        mat = np.array(
            [
                [0.4124564, 0.3575761, 0.1804375],
                [0.2126729, 0.7151522, 0.0721750],
                [0.0193339, 0.1191920, 0.9503041],
            ]
        )

        xyz = rgb_linear @ mat.T

        # Normalize by D65 white point
        xyz[:, :, 0] /= 0.95047
        xyz[:, :, 1] /= 1.00000
        xyz[:, :, 2] /= 1.08883

        # XYZ to LAB
        epsilon = 0.008856
        kappa = 903.3

        mask = xyz > epsilon
        f_xyz = np.where(mask, np.cbrt(xyz), (kappa * xyz + 16.0) / 116.0)

        lab = np.empty_like(rgb)
        lab[:, :, 0] = 116.0 * f_xyz[:, :, 1] - 16.0  # L
        lab[:, :, 1] = 500.0 * (f_xyz[:, :, 0] - f_xyz[:, :, 1])  # a
        lab[:, :, 2] = 200.0 * (f_xyz[:, :, 1] - f_xyz[:, :, 2])  # b

        return lab

    @staticmethod
    def _lab_to_rgb(lab: np.ndarray) -> np.ndarray:
        """
        Convert CIE LAB to RGB (0-1 float).

        Uses simplified LAB -> XYZ -> sRGB pipeline.
        """
        # LAB to XYZ
        fy = (lab[:, :, 0] + 16.0) / 116.0
        fx = lab[:, :, 1] / 500.0 + fy
        fz = fy - lab[:, :, 2] / 200.0

        epsilon = 0.008856
        kappa = 903.3

        x_mask = fx**3 > epsilon
        y_mask = lab[:, :, 0] > kappa * epsilon
        z_mask = fz**3 > epsilon

        x = np.where(x_mask, fx**3, (116.0 * fx - 16.0) / kappa)
        y = np.where(y_mask, fy**3, lab[:, :, 0] / kappa)
        z = np.where(z_mask, fz**3, (116.0 * fz - 16.0) / kappa)

        # Denormalize by D65 white point
        x *= 0.95047
        z *= 1.08883

        xyz = np.stack([x, y, z], axis=-1)

        # XYZ to linear RGB
        mat_inv = np.array(
            [
                [3.2404542, -1.5371385, -0.4985314],
                [-0.9692660, 1.8760108, 0.0415560],
                [0.0556434, -0.2040259, 1.0572252],
            ]
        )

        rgb_linear = xyz @ mat_inv.T

        # sRGB gamma
        rgb_linear = np.clip(rgb_linear, 0, None)
        mask = rgb_linear > 0.0031308
        rgb = np.where(mask, 1.055 * np.power(rgb_linear, 1.0 / 2.4) - 0.055, 12.92 * rgb_linear)

        return np.clip(rgb, 0.0, 1.0)
