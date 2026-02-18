"""Seed predefined pathology annotation labels

Revision ID: 004
Revises: 003
Create Date: 2026-02-16
"""

import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PATHOLOGY_LABELS = [
    {"name": "Tumeur", "color": "#e74c3c", "category": "diagnostic", "sort_order": 1},
    {"name": "Nécrose", "color": "#8e44ad", "category": "diagnostic", "sort_order": 2},
    {"name": "Inflammation", "color": "#e67e22", "category": "diagnostic", "sort_order": 3},
    {"name": "Stroma", "color": "#3498db", "category": "diagnostic", "sort_order": 4},
    {"name": "Tissu sain", "color": "#2ecc71", "category": "diagnostic", "sort_order": 5},
    {"name": "Marge de résection", "color": "#f39c12", "category": "structure", "sort_order": 10},
    {"name": "Embole vasculaire", "color": "#c0392b", "category": "structure", "sort_order": 11},
    {
        "name": "Invasion péri-nerveuse",
        "color": "#d35400",
        "category": "structure",
        "sort_order": 12,
    },
    {"name": "Artefact", "color": "#95a5a6", "category": "qualite", "sort_order": 20},
    {"name": "Zone floue", "color": "#7f8c8d", "category": "qualite", "sort_order": 21},
    {"name": "Pli de tissu", "color": "#bdc3c7", "category": "qualite", "sort_order": 22},
]


def upgrade() -> None:
    now = datetime.now(UTC).isoformat()
    for label in PATHOLOGY_LABELS:
        op.execute(
            sa.text(
                "INSERT INTO annotation_labels (id, name, color, category, sort_order, created_at) "
                "VALUES (:id, :name, :color, :category, :sort_order, :created_at) "
                "ON CONFLICT (name) DO NOTHING"
            ).bindparams(
                id=str(uuid.uuid4()),
                name=label["name"],
                color=label["color"],
                category=label["category"],
                sort_order=label["sort_order"],
                created_at=now,
            )
        )


def downgrade() -> None:
    names = [label["name"] for label in PATHOLOGY_LABELS]
    placeholders = ", ".join(f"'{n}'" for n in names)
    op.execute(sa.text(f"DELETE FROM annotation_labels WHERE name IN ({placeholders})"))
