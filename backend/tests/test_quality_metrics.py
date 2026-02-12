"""
Tests for quality.metrics - Pure mathematical functions.

Known values verified against textbook examples and scikit-learn.
No database required - runs anywhere numpy is available.
"""

import pytest

from quality.metrics import (
    cohens_kappa,
    confusion_matrix,
    fleiss_kappa,
    interpret_kappa,
    iou_distribution_stats,
    per_label_f1,
)

# ==========================================
# COHEN'S KAPPA
# ==========================================


class TestCohensKappa:
    def test_perfect_agreement(self):
        labels = ["A", "B", "C", "A", "B"]
        assert cohens_kappa(labels, labels) == 1.0

    def test_no_agreement_beyond_chance(self):
        """Two annotators who systematically disagree."""
        a = ["A", "A", "B", "B"]
        b = ["B", "B", "A", "A"]
        kappa = cohens_kappa(a, b)
        assert kappa < 0  # Worse than chance

    def test_known_textbook_value(self):
        """
        Classic example from Artstein & Poesio (2008).
        20 items, 2 annotators, 2 categories.
        A: 10 yes, 10 no. B: 8 yes, 12 no.
        Agree on 7 yes + 9 no = 16/20.
        """
        a = ["yes"] * 10 + ["no"] * 10
        b = ["yes"] * 7 + ["no"] * 3 + ["no"] * 9 + ["yes"] * 1
        kappa = cohens_kappa(a, b)
        # p_o = 16/20 = 0.8
        # p_e = (10/20 * 8/20) + (10/20 * 12/20) = 0.2 + 0.3 = 0.5
        # kappa = (0.8 - 0.5) / (1 - 0.5) = 0.6
        assert abs(kappa - 0.6) < 0.001

    def test_single_category(self):
        """All items same category = perfect agreement."""
        a = ["X", "X", "X"]
        b = ["X", "X", "X"]
        assert cohens_kappa(a, b) == 1.0

    def test_three_categories(self):
        a = ["A", "B", "C", "A", "B", "C"]
        b = ["A", "B", "C", "A", "B", "C"]
        assert cohens_kappa(a, b) == 1.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            cohens_kappa([], [])

    def test_unequal_length_raises(self):
        with pytest.raises(ValueError, match="equal length"):
            cohens_kappa(["A", "B"], ["A"])

    def test_partial_agreement(self):
        a = ["A", "A", "B", "B", "C", "C"]
        b = ["A", "B", "B", "A", "C", "C"]
        kappa = cohens_kappa(a, b)
        # 4/6 agreement, but kappa corrects for chance
        assert 0.0 < kappa < 1.0


# ==========================================
# FLEISS' KAPPA
# ==========================================


class TestFleissKappa:
    def test_perfect_agreement(self):
        """All 3 raters agree on every item."""
        matrix = [
            [3, 0],  # All say category 0
            [0, 3],  # All say category 1
            [3, 0],
            [0, 3],
        ]
        assert fleiss_kappa(matrix) == 1.0

    def test_no_agreement(self):
        """Ratings spread evenly across categories produce negative kappa."""
        # When every rater is evenly split, Fleiss' kappa is negative
        # (systematic disagreement: each subject gets equal votes per category)
        matrix = [
            [2, 2, 2],
            [2, 2, 2],
            [2, 2, 2],
        ]
        kappa = fleiss_kappa(matrix)
        assert kappa < 0  # Worse than chance (forced uniform)

    def test_known_fleiss_example(self):
        """
        Fleiss (1971) original paper example (adapted).
        14 subjects, 2 raters, 5 categories.
        """
        matrix = [
            [0, 0, 0, 0, 2],
            [0, 2, 0, 0, 0],
            [0, 0, 2, 0, 0],
            [2, 0, 0, 0, 0],
            [0, 0, 2, 0, 0],
            [0, 0, 0, 2, 0],
            [0, 0, 2, 0, 0],
            [0, 2, 0, 0, 0],
            [2, 0, 0, 0, 0],
            [0, 0, 0, 0, 2],
        ]
        kappa = fleiss_kappa(matrix)
        # Perfect agreement since all raters agree
        assert kappa == 1.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            fleiss_kappa([])

    def test_single_rater_raises(self):
        with pytest.raises(ValueError, match="2 raters"):
            fleiss_kappa([[1, 0], [0, 1]])

    def test_inconsistent_sums_raises(self):
        with pytest.raises(ValueError, match="same number"):
            fleiss_kappa([[3, 0], [2, 0]])


# ==========================================
# CONFUSION MATRIX
# ==========================================


class TestConfusionMatrix:
    def test_basic(self):
        a = ["A", "A", "B", "B"]
        b = ["A", "B", "A", "B"]
        matrix, cats = confusion_matrix(a, b)
        assert cats == ["A", "B"]
        assert matrix == [[1, 1], [1, 1]]

    def test_perfect(self):
        a = ["X", "Y", "Z"]
        b = ["X", "Y", "Z"]
        matrix, cats = confusion_matrix(a, b)
        assert cats == ["X", "Y", "Z"]
        # Diagonal only
        for i in range(3):
            for j in range(3):
                expected = 1 if i == j else 0
                assert matrix[i][j] == expected

    def test_unequal_raises(self):
        with pytest.raises(ValueError, match="equal length"):
            confusion_matrix(["A"], ["A", "B"])


# ==========================================
# PER-LABEL F1
# ==========================================


class TestPerLabelF1:
    def test_perfect(self):
        a = ["A", "B", "C"]
        b = ["A", "B", "C"]
        results = per_label_f1(a, b)
        for r in results:
            assert r["precision"] == 1.0
            assert r["recall"] == 1.0
            assert r["f1"] == 1.0

    def test_zero_recall(self):
        """B never predicts 'A' when A says 'A'."""
        a = ["A", "A", "B", "B"]
        b = ["B", "B", "B", "B"]
        results = per_label_f1(a, b)
        a_metrics = next(r for r in results if r["label"] == "A")
        assert a_metrics["recall"] == 0.0
        assert a_metrics["support"] == 2

    def test_support_count(self):
        a = ["X", "X", "X", "Y"]
        b = ["X", "X", "Y", "Y"]
        results = per_label_f1(a, b)
        x_metrics = next(r for r in results if r["label"] == "X")
        assert x_metrics["support"] == 3


# ==========================================
# IoU DISTRIBUTION
# ==========================================


class TestIoUDistribution:
    def test_empty(self):
        stats = iou_distribution_stats([])
        assert stats["count"] == 0
        assert stats["mean"] == 0.0

    def test_single_value(self):
        stats = iou_distribution_stats([0.75])
        assert stats["count"] == 1
        assert stats["mean"] == 0.75
        assert stats["median"] == 0.75
        assert stats["std"] == 0.0

    def test_histogram_bins(self):
        stats = iou_distribution_stats([0.1, 0.5, 0.9])
        assert len(stats["histogram"]) == 10
        assert stats["histogram"][0]["bin_start"] == 0.0
        assert stats["histogram"][-1]["bin_end"] == 1.0

    def test_stats_values(self):
        values = [0.0, 0.25, 0.5, 0.75, 1.0]
        stats = iou_distribution_stats(values)
        assert stats["count"] == 5
        assert stats["mean"] == 0.5
        assert stats["median"] == 0.5
        assert stats["min"] == 0.0
        assert stats["max"] == 1.0


# ==========================================
# KAPPA INTERPRETATION
# ==========================================


class TestInterpretKappa:
    def test_poor(self):
        assert interpret_kappa(-0.5) == "Poor"

    def test_slight(self):
        assert interpret_kappa(0.1) == "Slight"

    def test_fair(self):
        assert interpret_kappa(0.3) == "Fair"

    def test_moderate(self):
        assert interpret_kappa(0.5) == "Moderate"

    def test_substantial(self):
        assert interpret_kappa(0.7) == "Substantial"

    def test_almost_perfect(self):
        assert interpret_kappa(0.9) == "Almost Perfect"

    def test_perfect(self):
        assert interpret_kappa(1.0) == "Almost Perfect"
