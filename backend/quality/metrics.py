"""
Quality Metrics - Pure mathematical functions for inter-annotator agreement.

All functions are stateless and operate on plain Python/numpy data structures.
No database or I/O dependencies - fully unit-testable in isolation.

References:
    - Cohen's kappa: Cohen, 1960 (doi:10.1177/001316446002000104)
    - Fleiss' kappa: Fleiss, 1971 (doi:10.1037/h0031619)
    - Landis & Koch scale: Landis & Koch, 1977
"""

from typing import Dict, List, Tuple

import numpy as np

# ==========================================
# KAPPA STATISTICS
# ==========================================


def cohens_kappa(labels_a: List[str], labels_b: List[str]) -> float:
    """
    Compute Cohen's kappa for two annotators.

    Measures agreement between two raters who each classify N items
    into C mutually exclusive categories, correcting for chance agreement.

    Args:
        labels_a: Labels assigned by annotator A (length N).
        labels_b: Labels assigned by annotator B (length N).

    Returns:
        Kappa coefficient in [-1, 1]. 1 = perfect agreement,
        0 = chance agreement, negative = worse than chance.

    Raises:
        ValueError: If input lists have different lengths or are empty.
    """
    if len(labels_a) != len(labels_b):
        msg = f"Label lists must have equal length: {len(labels_a)} != {len(labels_b)}"
        raise ValueError(msg)
    if len(labels_a) == 0:
        msg = "Label lists must not be empty"
        raise ValueError(msg)

    n = len(labels_a)
    categories = sorted(set(labels_a) | set(labels_b))

    if len(categories) == 1:
        # Both annotators always agree on the single category
        return 1.0

    # Build confusion matrix
    cat_to_idx = {c: i for i, c in enumerate(categories)}
    matrix = np.zeros((len(categories), len(categories)), dtype=np.float64)
    for a, b in zip(labels_a, labels_b, strict=False):
        matrix[cat_to_idx[a], cat_to_idx[b]] += 1

    # Observed agreement (proportion on diagonal)
    p_o = np.trace(matrix) / n

    # Expected agreement (marginal products)
    row_sums = matrix.sum(axis=1)
    col_sums = matrix.sum(axis=0)
    p_e = np.sum(row_sums * col_sums) / (n * n)

    if p_e == 1.0:
        # Degenerate case: all items in one category
        return 1.0

    return float((p_o - p_e) / (1.0 - p_e))


def fleiss_kappa(rating_matrix: List[List[int]]) -> float:
    """
    Compute Fleiss' kappa for multiple raters.

    Generalizes Cohen's kappa to any fixed number of raters.
    Each row is a subject (item), each column is a category.
    Cell values are the number of raters who assigned that category.

    Args:
        rating_matrix: N x C matrix where N = subjects, C = categories.
            Each row must sum to the same value (number of raters).

    Returns:
        Kappa coefficient in [-1, 1].

    Raises:
        ValueError: If matrix is empty or rows have inconsistent sums.
    """
    mat = np.array(rating_matrix, dtype=np.float64)

    if mat.size == 0:
        msg = "Rating matrix must not be empty"
        raise ValueError(msg)

    n_subjects, n_categories = mat.shape

    if n_subjects == 0 or n_categories == 0:
        msg = "Rating matrix must have subjects and categories"
        raise ValueError(msg)

    # Number of raters per subject (must be constant)
    n_raters = mat[0].sum()
    if n_raters < 2:
        msg = "Need at least 2 raters"
        raise ValueError(msg)

    row_sums = mat.sum(axis=1)
    if not np.allclose(row_sums, n_raters):
        msg = "All rows must sum to the same number of raters"
        raise ValueError(msg)

    # Proportion of assignments to each category
    p_j = mat.sum(axis=0) / (n_subjects * n_raters)

    # P_e: expected agreement by chance
    p_e = float(np.sum(p_j**2))

    if p_e == 1.0:
        return 1.0

    # P_i for each subject: proportion of agreeing pairs
    p_i = (np.sum(mat**2, axis=1) - n_raters) / (n_raters * (n_raters - 1))

    # P_bar: mean observed agreement
    p_bar = float(np.mean(p_i))

    return float((p_bar - p_e) / (1.0 - p_e))


# ==========================================
# CONFUSION MATRIX
# ==========================================


def confusion_matrix(labels_a: List[str], labels_b: List[str]) -> Tuple[List[List[int]], List[str]]:
    """
    Build confusion matrix for two annotators.

    Args:
        labels_a: Labels from annotator A.
        labels_b: Labels from annotator B.

    Returns:
        Tuple of (matrix, categories) where matrix[i][j] = count of items
        annotator A labeled as categories[i] and B labeled as categories[j].
    """
    if len(labels_a) != len(labels_b):
        msg = "Label lists must have equal length"
        raise ValueError(msg)

    categories = sorted(set(labels_a) | set(labels_b))
    cat_to_idx = {c: i for i, c in enumerate(categories)}
    n = len(categories)
    matrix = [[0] * n for _ in range(n)]

    for a, b in zip(labels_a, labels_b, strict=False):
        matrix[cat_to_idx[a]][cat_to_idx[b]] += 1

    return matrix, categories


# ==========================================
# PER-LABEL METRICS (F1, PRECISION, RECALL)
# ==========================================


def per_label_f1(labels_a: List[str], labels_b: List[str]) -> List[Dict[str, object]]:
    """
    Compute precision, recall, and F1 per label.

    Treats annotator A as ground truth, annotator B as prediction.

    Args:
        labels_a: Ground truth labels.
        labels_b: Predicted labels.

    Returns:
        List of dicts: [{label, precision, recall, f1, support}, ...]
        where support = count in ground truth.
    """
    if len(labels_a) != len(labels_b):
        msg = "Label lists must have equal length"
        raise ValueError(msg)

    categories = sorted(set(labels_a) | set(labels_b))
    results = []

    for cat in categories:
        tp = sum(1 for a, b in zip(labels_a, labels_b, strict=False) if a == cat and b == cat)
        fp = sum(1 for a, b in zip(labels_a, labels_b, strict=False) if a != cat and b == cat)
        fn = sum(1 for a, b in zip(labels_a, labels_b, strict=False) if a == cat and b != cat)
        support = tp + fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        results.append(
            {
                "label": cat,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": support,
            }
        )

    return results


# ==========================================
# IoU DISTRIBUTION
# ==========================================


def iou_distribution_stats(iou_values: List[float]) -> Dict[str, object]:
    """
    Compute descriptive statistics for a list of IoU values.

    Args:
        iou_values: List of IoU scores in [0, 1].

    Returns:
        Dict with mean, median, std, min, max, histogram (10 bins), count.
    """
    if not iou_values:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "histogram": [],
        }

    arr = np.array(iou_values, dtype=np.float64)
    # 10 bins from 0.0 to 1.0
    counts, bin_edges = np.histogram(arr, bins=10, range=(0.0, 1.0))

    histogram = []
    for i in range(len(counts)):
        histogram.append(
            {
                "bin_start": round(float(bin_edges[i]), 2),
                "bin_end": round(float(bin_edges[i + 1]), 2),
                "count": int(counts[i]),
            }
        )

    return {
        "count": len(iou_values),
        "mean": round(float(np.mean(arr)), 4),
        "median": round(float(np.median(arr)), 4),
        "std": round(float(np.std(arr)), 4),
        "min": round(float(np.min(arr)), 4),
        "max": round(float(np.max(arr)), 4),
        "histogram": histogram,
    }


# ==========================================
# KAPPA INTERPRETATION
# ==========================================

LANDIS_KOCH_SCALE = [
    (-1.0, 0.0, "Poor"),
    (0.0, 0.20, "Slight"),
    (0.20, 0.40, "Fair"),
    (0.40, 0.60, "Moderate"),
    (0.60, 0.80, "Substantial"),
    (0.80, 1.01, "Almost Perfect"),  # 1.01 to include 1.0
]


def interpret_kappa(kappa: float) -> str:
    """
    Interpret kappa value using Landis & Koch (1977) scale.

    Args:
        kappa: Kappa coefficient.

    Returns:
        Interpretation string (e.g. "Substantial").
    """
    for low, high, label in LANDIS_KOCH_SCALE:
        if low <= kappa < high:
            return label
    return "Poor" if kappa < 0 else "Almost Perfect"
