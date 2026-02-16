"""
Tests for FeedbackCollector service.

Uses mocked async DB sessions to verify aggregation logic,
threshold detection, and rejection rate computation.
"""

import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Ensure sqlalchemy + models.correction are importable via mocks so that
# the lazy imports inside FeedbackCollector.get_stats() succeed even when
# the real packages are not installed in the test environment.
# ---------------------------------------------------------------------------

class _Column:
    """Mimics a SQLAlchemy column for comparison-based query building."""
    def __init__(self, name="col"):
        self._name = name

    def __ge__(self, other):
        return MagicMock(name=f"{self._name}_ge")

    def __le__(self, other):
        return MagicMock(name=f"{self._name}_le")

    def __eq__(self, other):
        return MagicMock(name=f"{self._name}_eq")

    def __ne__(self, other):
        return MagicMock(name=f"{self._name}_ne")

    def __hash__(self):
        return id(self)


class _FakeCorrection:
    """Fake Correction ORM model for testing."""
    id = _Column("id")
    model_name = _Column("model_name")
    correction_type = _Column("correction_type")
    created_at = _Column("created_at")


def _ensure_mock_modules():
    """Inject mock modules for sqlalchemy and models.correction if absent."""
    mods_needed = {}

    # --- sqlalchemy hierarchy ---------------------------------------------------
    if "sqlalchemy" not in sys.modules:
        sa = types.ModuleType("sqlalchemy")
        sa.select = MagicMock(name="select")
        sa.func = MagicMock(name="func")
        sa.case = MagicMock(name="case")
        mods_needed["sqlalchemy"] = sa

    for sub in (
        "sqlalchemy.orm",
        "sqlalchemy.ext",
        "sqlalchemy.ext.asyncio",
        "sqlalchemy.dialects",
        "sqlalchemy.dialects.postgresql",
    ):
        if sub not in sys.modules:
            mods_needed[sub] = types.ModuleType(sub)

    # --- core.database (needed by models.correction) ----------------------------
    if "core" not in sys.modules:
        core = types.ModuleType("core")
        mods_needed["core"] = core
    if "core.database" not in sys.modules:
        core_db = types.ModuleType("core.database")
        core_db.Base = type("Base", (), {})
        mods_needed["core.database"] = core_db

    # --- models.correction -------------------------------------------------------
    if "models" not in sys.modules:
        models_mod = types.ModuleType("models")
        mods_needed["models"] = models_mod
    if "models.correction" not in sys.modules:
        mc = types.ModuleType("models.correction")
        mc.Correction = _FakeCorrection
        mods_needed["models.correction"] = mc

    sys.modules.update(mods_needed)


_ensure_mock_modules()

from services.feedback_collector import FeedbackCollector, FeedbackStats  # noqa: E402


class TestFeedbackCollector:
    @pytest.mark.asyncio
    async def test_empty_stats(self):
        """No corrections -> empty list."""
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.execute.return_value = result_mock

        collector = FeedbackCollector()
        stats = await collector.get_stats(session)
        assert stats == []

    @pytest.mark.asyncio
    async def test_aggregation(self):
        """Verify correct aggregation of correction types."""
        session = AsyncMock()
        row = MagicMock()
        row.model_name = "ctranspath"
        row.total = 10
        row.confirmed = 5
        row.rejected = 3
        row.refined = 1
        row.relabeled = 1
        result_mock = MagicMock()
        result_mock.all.return_value = [row]
        session.execute.return_value = result_mock

        collector = FeedbackCollector()
        stats = await collector.get_stats(session)
        assert len(stats) == 1
        assert stats[0].total_corrections == 10
        assert stats[0].confirmed == 5
        assert stats[0].rejected == 3
        assert stats[0].rejection_rate == 0.3

    @pytest.mark.asyncio
    async def test_retrain_threshold(self):
        """100+ corrections -> needs_retrain=True."""
        session = AsyncMock()
        row = MagicMock()
        row.model_name = "phikon-v2"
        row.total = 150
        row.confirmed = 100
        row.rejected = 30
        row.refined = 10
        row.relabeled = 10
        result_mock = MagicMock()
        result_mock.all.return_value = [row]
        session.execute.return_value = result_mock

        collector = FeedbackCollector()
        stats = await collector.get_stats(session)
        assert stats[0].needs_retrain is True

    @pytest.mark.asyncio
    async def test_high_rejection_alert(self):
        """31% rejection rate -> high_rejection=True."""
        session = AsyncMock()
        row = MagicMock()
        row.model_name = "resnet50"
        row.total = 100
        row.confirmed = 60
        row.rejected = 31
        row.refined = 5
        row.relabeled = 4
        result_mock = MagicMock()
        result_mock.all.return_value = [row]
        session.execute.return_value = result_mock

        collector = FeedbackCollector()
        stats = await collector.get_stats(session)
        assert stats[0].high_rejection is True
        assert stats[0].rejection_rate == 0.31
