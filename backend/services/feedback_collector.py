"""
FeedbackCollector — Aggregates pathologist corrections with sliding window stats.

Reads from the corrections table with a configurable sliding window
(default: last 7 days) grouped by model_name. Computes rejection rate,
retrain threshold, and high-rejection alerts.

Usage:
    collector = FeedbackCollector()
    async with get_db_context() as session:
        stats = await collector.get_stats(session, model_name="ctranspath")
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Configurable thresholds
FEEDBACK_RETRAIN_THRESHOLD = 100  # corrections before suggesting retrain
FEEDBACK_REJECTION_ALERT = 0.3  # 30% rejection rate triggers alert
FEEDBACK_WINDOW_DAYS = 7  # sliding window size


@dataclass
class FeedbackStats:
    """Aggregated feedback statistics for a model."""

    model_name: str
    window_days: int
    total_corrections: int
    confirmed: int
    rejected: int
    refined: int
    relabeled: int
    rejection_rate: float  # rejected / total
    needs_retrain: bool  # total >= threshold
    high_rejection: bool  # rejection_rate >= alert threshold
    computed_at: str  # ISO timestamp


class FeedbackCollector:
    """Aggregates pathologist corrections and computes threshold alerts.

    Reads from the corrections table with a sliding window
    (last N days) grouped by model_name.
    """

    def __init__(
        self,
        retrain_threshold: int = FEEDBACK_RETRAIN_THRESHOLD,
        rejection_alert: float = FEEDBACK_REJECTION_ALERT,
        window_days: int = FEEDBACK_WINDOW_DAYS,
    ):
        self.retrain_threshold = retrain_threshold
        self.rejection_alert = rejection_alert
        self.window_days = window_days

    async def get_stats(self, db_session, model_name: str = None) -> list:
        """Compute sliding-window stats per model.

        Args:
            db_session: AsyncSession
            model_name: Optional filter for specific model

        Returns:
            List of FeedbackStats, one per model_name
        """
        from sqlalchemy import case as sql_case
        from sqlalchemy import func, select

        from models.correction import Correction

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.window_days)

        query = (
            select(
                Correction.model_name,
                func.count(Correction.id).label("total"),
                func.sum(sql_case((Correction.correction_type == "confirmed", 1), else_=0)).label(
                    "confirmed"
                ),
                func.sum(sql_case((Correction.correction_type == "rejected", 1), else_=0)).label(
                    "rejected"
                ),
                func.sum(sql_case((Correction.correction_type == "refined", 1), else_=0)).label(
                    "refined"
                ),
                func.sum(sql_case((Correction.correction_type == "relabeled", 1), else_=0)).label(
                    "relabeled"
                ),
            )
            .where(Correction.created_at >= cutoff)
            .group_by(Correction.model_name)
        )

        if model_name:
            query = query.where(Correction.model_name == model_name)

        result = await db_session.execute(query)
        rows = result.all()

        stats = []
        for row in rows:
            total = row.total or 0
            rejected = row.rejected or 0
            rejection_rate = rejected / total if total > 0 else 0.0

            stats.append(
                FeedbackStats(
                    model_name=row.model_name or "unknown",
                    window_days=self.window_days,
                    total_corrections=total,
                    confirmed=row.confirmed or 0,
                    rejected=rejected,
                    refined=row.refined or 0,
                    relabeled=row.relabeled or 0,
                    rejection_rate=round(rejection_rate, 4),
                    needs_retrain=total >= self.retrain_threshold,
                    high_rejection=rejection_rate >= self.rejection_alert,
                    computed_at=datetime.now(timezone.utc).isoformat(),
                )
            )

        return stats
