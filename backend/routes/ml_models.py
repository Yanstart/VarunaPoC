"""ML Models Registry — CRUD API.

Backs the `ml_models` table (migration 010). All write endpoints are
restricted to `ADMIN_TECHNIQUE`. Reads are open to any authenticated
caller within the tenant scope (foundation models tagged `tenant_id =
'global'` are visible to every tenant).

Issue: #370
"""

import logging
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.audit import AuditEvents, log_audit_event
from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from core.database import get_db
from core.tenant import get_current_tenant
from models.ml_model import MLModel
from schemas.ml_model import License, MLModelCreate, MLModelOut, MLModelUpdate, TaskType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml-models", tags=["ML Models Registry"])

GLOBAL_TENANT = "global"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _persist_new_model(
    payload: MLModelCreate,
    target_tenant: str,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession,
) -> MLModel:
    """Common write path shared by `create_ml_model` and `create_global_ml_model`.

    The tenant is decided by the caller — never read from the request payload —
    which collapses the cross-tenant injection vector entirely.
    """
    obj = MLModel(
        tenant_id=target_tenant,
        name=payload.name,
        version=payload.version,
        framework=payload.framework,
        architecture=payload.architecture,
        task_type=payload.task_type.value,
        input_shape=payload.input_shape.model_dump() if payload.input_shape else None,
        embedding_dim=payload.embedding_dim,
        checkpoint_hash=payload.checkpoint_hash,
        checkpoint_uri=payload.checkpoint_uri,
        mlflow_run_id=payload.mlflow_run_id,
        mlflow_experiment_id=payload.mlflow_experiment_id,
        mlflow_model_uri=payload.mlflow_model_uri,
        license=payload.license.value if payload.license else None,
        usage_constraints=payload.usage_constraints,
        description=payload.description,
        metadata_extra=payload.metadata_extra,
        registered_by=current_user.username,
    )
    db.add(obj)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Model '{payload.name}' v{payload.version} already exists "
                f"in tenant '{target_tenant}'."
            ),
        ) from exc
    await db.refresh(obj)
    logger.info(
        "ML model registered: id=%s name=%s version=%s tenant=%s by=%s",
        obj.id,
        obj.name,
        obj.version,
        obj.tenant_id,
        current_user.username,
    )
    await log_audit_event(
        event_type=AuditEvents.ML_MODEL_REGISTERED,
        action="CREATE",
        user=current_user,
        request=request,
        resource_type="ml_model",
        resource_id=str(obj.id),
        details={
            "name": obj.name,
            "version": obj.version,
            "tenant_id": obj.tenant_id,
            "task_type": obj.task_type,
            "license": obj.license,
            "mlflow_run_id": obj.mlflow_run_id,
        },
        data_classification="internal",
    )
    return obj


def _safe_model_out(orm_obj: MLModel) -> MLModelOut:
    """Build MLModelOut from an ORM row, with graceful fallback on out-of-enum license.

    Defense-in-depth: the DB column `license` is a free VARCHAR (decision B),
    so a row written via raw SQL may carry a value not listed in the License
    enum. Without this guard, Pydantic would raise ValidationError at response
    time and return a 500 — we want a 200 with the literal string returned in
    a sidecar field instead, so the caller (UI / audit) still sees the model.
    """
    license_value = orm_obj.license
    try:
        return MLModelOut.model_validate(orm_obj)
    except ValidationError:
        # Coerce the offending license back to None for the structured field
        # and surface the raw value in metadata_extra for audit visibility.
        # Only ValidationError is rescued: other exceptions (DB, network) must
        # propagate so they are not silently hidden under "bad license".
        extra = dict(orm_obj.metadata_extra or {})
        extra.setdefault("license_raw", license_value)
        logger.warning(
            "Model %s has an out-of-enum license=%r; surfaced via metadata_extra.license_raw",
            orm_obj.id,
            license_value,
        )
        snapshot = MLModelOut.model_construct(
            id=orm_obj.id,
            tenant_id=orm_obj.tenant_id,
            name=orm_obj.name,
            version=orm_obj.version,
            framework=orm_obj.framework,
            architecture=orm_obj.architecture,
            task_type=orm_obj.task_type,
            input_shape=orm_obj.input_shape,
            embedding_dim=orm_obj.embedding_dim,
            checkpoint_hash=orm_obj.checkpoint_hash,
            checkpoint_uri=orm_obj.checkpoint_uri,
            mlflow_run_id=orm_obj.mlflow_run_id,
            mlflow_experiment_id=orm_obj.mlflow_experiment_id,
            mlflow_model_uri=orm_obj.mlflow_model_uri,
            license=None,
            usage_constraints=orm_obj.usage_constraints,
            description=orm_obj.description,
            metadata_extra=extra,
            registered_by=orm_obj.registered_by,
            registered_at=orm_obj.registered_at,
            deployed_at=orm_obj.deployed_at,
            retired_at=orm_obj.retired_at,
            updated_at=orm_obj.updated_at,
        )
        return snapshot


async def _get_or_404(db: AsyncSession, model_id: UUID, tenant_id: str) -> MLModel:
    """Fetch a model accessible to the tenant, or 404."""
    stmt = select(MLModel).where(
        MLModel.id == model_id,
        or_(MLModel.tenant_id == tenant_id, MLModel.tenant_id == GLOBAL_TENANT),
    )
    obj = (await db.execute(stmt)).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail=f"ml_model {model_id} not found")
    return obj


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=MLModelOut, status_code=201)
async def create_ml_model(
    payload: MLModelCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
) -> MLModelOut:
    """Register a new model under the caller's tenant.

    Identity is `(tenant_id, name, version)`. A duplicate returns 409.
    To register a model shared across tenants (foundation models), call
    POST /api/v1/ml-models/global instead.
    """
    obj = await _persist_new_model(payload, tenant_id, current_user, request, db)
    return _safe_model_out(obj)


@router.post("/global", response_model=MLModelOut, status_code=201)
async def create_global_ml_model(
    payload: MLModelCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
) -> MLModelOut:
    """Register a model in the `global` tenant — visible to every tenant.

    Use this for foundation models (UNI, CONCH, Virchow, GigaPath, …) and
    public checkpoints whose lineage is shared across the platform.
    """
    obj = await _persist_new_model(payload, GLOBAL_TENANT, current_user, request, db)
    return _safe_model_out(obj)


@router.get("", response_model=list[MLModelOut])
async def list_ml_models(
    task_type: Optional[TaskType] = Query(None, description="Filter by ML task type"),
    include_retired: bool = Query(False, description="Include retired models in results"),
    only_deployed: bool = Query(False, description="Restrict to currently deployed models"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
) -> list[MLModelOut]:
    """List models visible to the caller's tenant (plus globals)."""
    stmt = select(MLModel).where(
        or_(MLModel.tenant_id == tenant_id, MLModel.tenant_id == GLOBAL_TENANT),
    )
    if task_type is not None:
        stmt = stmt.where(MLModel.task_type == task_type.value)
    if not include_retired:
        stmt = stmt.where(MLModel.retired_at.is_(None))
    if only_deployed:
        stmt = stmt.where(MLModel.deployed_at.is_not(None))
        stmt = stmt.where(MLModel.retired_at.is_(None))
    stmt = stmt.order_by(MLModel.registered_at.desc()).limit(limit).offset(offset)

    rows = (await db.execute(stmt)).scalars().all()
    return [_safe_model_out(r) for r in rows]


@router.get("/{model_id}", response_model=MLModelOut)
async def get_ml_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
) -> MLModelOut:
    """Retrieve a single model by id."""
    obj = await _get_or_404(db, model_id, tenant_id)
    return _safe_model_out(obj)


@router.patch("/{model_id}", response_model=MLModelOut)
async def patch_ml_model(
    model_id: UUID,
    payload: MLModelUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
) -> MLModelOut:
    """Patch mutable fields of a model. Identity (name, version, task_type)
    is immutable — register a new row instead."""
    obj = await _get_or_404(db, model_id, tenant_id)

    # Pydantic v2 already serializes sub-models to dicts and enums to their
    # value in `model_dump`, so the resulting dict is ready to assign onto
    # the ORM columns as-is.
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc.orig)) from exc
    await db.refresh(obj)
    await log_audit_event(
        event_type=AuditEvents.ML_MODEL_UPDATED,
        action="UPDATE",
        user=current_user,
        request=request,
        resource_type="ml_model",
        resource_id=str(obj.id),
        details={"changed_fields": sorted(data.keys())},
        data_classification="internal",
    )
    return _safe_model_out(obj)


@router.post("/{model_id}/deploy", response_model=MLModelOut)
async def deploy_ml_model(
    model_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
) -> MLModelOut:
    """Mark a model as deployed (sets `deployed_at` if not already set).

    Idempotent: re-deploying a deployed model is a no-op. Cannot deploy a
    retired model — register a new row instead.
    """
    obj = await _get_or_404(db, model_id, tenant_id)
    if obj.retired_at is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot deploy a retired model. Register a new version instead.",
        )
    if obj.deployed_at is None:
        obj.deployed_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(obj)
        logger.info("ML model deployed: %s by %s", obj.id, current_user.username)
        await log_audit_event(
            event_type=AuditEvents.ML_MODEL_DEPLOYED,
            action="UPDATE",
            user=current_user,
            request=request,
            resource_type="ml_model",
            resource_id=str(obj.id),
            details={"name": obj.name, "version": obj.version, "tenant_id": obj.tenant_id},
            data_classification="internal",
        )
    return _safe_model_out(obj)


@router.post("/{model_id}/retire", response_model=MLModelOut)
async def retire_ml_model(
    model_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
) -> MLModelOut:
    """Soft-delete a model by setting `retired_at`. Existing FK references
    (annotations.source_model_id, corrections.model_id) keep the model
    readable for audit."""
    obj = await _get_or_404(db, model_id, tenant_id)
    if obj.retired_at is None:
        obj.retired_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(obj)
        logger.info("ML model retired: %s by %s", obj.id, current_user.username)
        await log_audit_event(
            event_type=AuditEvents.ML_MODEL_RETIRED,
            action="DELETE",
            user=current_user,
            request=request,
            resource_type="ml_model",
            resource_id=str(obj.id),
            details={"name": obj.name, "version": obj.version, "tenant_id": obj.tenant_id},
            data_classification="internal",
            level="WARNING",
        )
    return _safe_model_out(obj)


# DELETE is an alias for /retire to match REST expectations while preserving
# the audit trail (no physical row deletion in this registry).
@router.delete("/{model_id}", response_model=MLModelOut)
async def delete_ml_model(
    model_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
) -> MLModelOut:
    """DELETE = soft retire. The row is never physically removed."""
    return await retire_ml_model(model_id, request, db, current_user, tenant_id)
