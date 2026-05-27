"""Seed the ml_models registry with the foundation models actively used by Varuna.

Idempotent: re-runnable. Skips models already present (matched by
`(tenant_id, name, version)`).

The seed targets the models actually exercised by the running stack:
  * Phikon-v2 — the default Slideflow feature extractor (`ML_PROVIDER=slideflow`)

Foundation models that will be added by issue #346 (UNI, CONCH, Virchow,
GigaPath, mSTAR) are NOT seeded here — that issue carries its own
registration step inside each adapter.

Usage (inside the backend container):
    docker exec varuna-backend python -m scripts.seed_ml_models

Run from CI as a post-migration step to ensure a clean install has the
baseline model entries in place. Safe to chain after `alembic upgrade head`.
"""

import asyncio
import logging
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session
from models.ml_model import MLModel

logger = logging.getLogger(__name__)


# Each entry is a row payload. Identity is (tenant_id, name, version).
_SEED_ROWS: list[dict] = [
    {
        "tenant_id": "global",
        "name": "phikon-v2",
        "version": "2025.02",
        "framework": "pytorch",
        "architecture": "ViT-B/16 (Phikon)",
        "task_type": "feature_extractor",
        "input_shape": {"h": 224, "w": 224, "c": 3},
        "embedding_dim": 768,
        "checkpoint_hash": None,
        "checkpoint_uri": "hf://owkin/phikon-v2",
        "mlflow_run_id": None,
        "mlflow_experiment_id": None,
        "mlflow_model_uri": None,
        "license": "cc-by-nc-nd-4.0",
        "usage_constraints": {
            "commercial": False,
            "derivative_works": False,
            "phi": True,
        },
        "description": (
            "Owkin Phikon-v2 — open histology-pretrained feature extractor "
            "(Filiot et al., 2024). Used by the Slideflow ML provider as the "
            "default backbone for tissue embedding and similarity search."
        ),
        "registered_by": "system:seed",
        "metadata_extra": {
            "source": "huggingface",
            "paper": "https://arxiv.org/abs/2409.09173",
            "seeded_by": "scripts/seed_ml_models.py",
        },
    },
]


async def _seed_one(session: AsyncSession, row: dict) -> tuple[str, bool]:
    """Return (model_label, inserted). `inserted=False` if row already existed."""
    label = f"{row['name']}@{row['version']} ({row['tenant_id']})"
    exists = (
        await session.execute(
            select(MLModel).where(
                MLModel.tenant_id == row["tenant_id"],
                MLModel.name == row["name"],
                MLModel.version == row["version"],
            )
        )
    ).scalar_one_or_none()
    if exists is not None:
        return label, False
    session.add(MLModel(**row))
    return label, True


async def seed() -> dict[str, int]:
    """Run the seed. Returns {inserted, skipped}."""
    inserted, skipped = 0, 0
    async with async_session() as session, session.begin():
        for row in _SEED_ROWS:
            label, was_inserted = await _seed_one(session, row)
            if was_inserted:
                inserted += 1
                logger.info("Seed: inserted %s", label)
            else:
                skipped += 1
                logger.info("Seed: skipped %s (already present)", label)
    return {"inserted": inserted, "skipped": skipped, "total": len(_SEED_ROWS)}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    try:
        result = asyncio.run(seed())
    except Exception:
        logger.exception("Seed failed")
        return 1
    logger.info(
        "Seed complete: inserted=%d skipped=%d total=%d",
        result["inserted"],
        result["skipped"],
        result["total"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
