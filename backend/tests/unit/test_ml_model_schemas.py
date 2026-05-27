"""Unit tests for backend/schemas/ml_model.py.

Validates the Pydantic contract surface for issue #370:
  - Strict TaskType / License enums at the API boundary
  - Custom validators (OTHER → require description, extractor → require dim)
  - Computed fields (is_active, is_deployed, commercial_use_allowed, open_source)
  - MLModelOut.from_attributes against an ORM-shaped object
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from schemas.ml_model import (
    License,
    MLModelCreate,
    MLModelOut,
    MLModelUpdate,
    TaskType,
    is_commercial_use_allowed_for,
    is_open_source,
)

# ----------------------------------------------------------------------
# MLModelCreate — happy paths
# ----------------------------------------------------------------------


def test_create_feature_extractor_minimum_fields():
    """Smallest valid extractor payload."""
    m = MLModelCreate(
        name="phikon-v2",
        version="2026.05",
        task_type=TaskType.FEATURE_EXTRACTOR,
        embedding_dim=768,
    )
    assert m.task_type == TaskType.FEATURE_EXTRACTOR
    assert m.embedding_dim == 768
    assert m.license is None


def test_create_classifier_no_embedding_required():
    """Classifiers do not require embedding_dim."""
    m = MLModelCreate(
        name="tumor-classifier",
        version="1.0.0",
        task_type=TaskType.CLASSIFIER,
    )
    assert m.task_type == TaskType.CLASSIFIER
    assert m.embedding_dim is None


def test_create_with_mlflow_lineage():
    """MLflow fields round-trip."""
    m = MLModelCreate(
        name="resnet50-finetuned",
        version="1.0.0",
        task_type=TaskType.CLASSIFIER,
        mlflow_run_id="abc123def456",
        mlflow_experiment_id="42",
        mlflow_model_uri="models:/resnet50-finetuned/Production",
    )
    assert m.mlflow_run_id == "abc123def456"
    assert m.mlflow_model_uri == "models:/resnet50-finetuned/Production"


def test_create_input_shape_validated():
    """InputShape sub-model rejects non-positive dims."""
    with pytest.raises(ValidationError):
        MLModelCreate(
            name="bad",
            version="0",
            task_type=TaskType.CLASSIFIER,
            input_shape={"h": 0, "w": 224, "c": 3},
        )


# ----------------------------------------------------------------------
# MLModelCreate — validators
# ----------------------------------------------------------------------


def test_create_extractor_without_embedding_dim_rejected():
    """Validator: feature_extractor must declare embedding_dim."""
    with pytest.raises(ValidationError, match="embedding_dim"):
        MLModelCreate(
            name="bad-extractor",
            version="1.0",
            task_type=TaskType.FEATURE_EXTRACTOR,
        )


def test_create_license_other_without_description_rejected():
    """Validator: license=OTHER demands a non-empty description."""
    with pytest.raises(ValidationError, match="OTHER"):
        MLModelCreate(
            name="exotic",
            version="0.1",
            task_type=TaskType.CLASSIFIER,
            license=License.OTHER,
        )


def test_create_license_other_with_blank_description_rejected():
    """Whitespace-only description does not satisfy the OTHER rule."""
    with pytest.raises(ValidationError, match="OTHER"):
        MLModelCreate(
            name="exotic",
            version="0.1",
            task_type=TaskType.CLASSIFIER,
            license=License.OTHER,
            description="   ",
        )


def test_create_license_other_with_description_accepted():
    """Filled description satisfies the OTHER rule."""
    m = MLModelCreate(
        name="exotic",
        version="0.1",
        task_type=TaskType.CLASSIFIER,
        license=License.OTHER,
        description="Custom in-house dual MIT + research-only clause",
    )
    assert m.license == License.OTHER


def test_create_invalid_task_type_rejected():
    """Strict enum at the boundary: unknown task_type is 422."""
    with pytest.raises(ValidationError):
        MLModelCreate(
            name="x",
            version="1",
            task_type="not_a_task",  # type: ignore[arg-type]
        )


def test_create_negative_embedding_dim_rejected():
    """Pydantic enforces ge=0 even when the DB CHECK would too."""
    with pytest.raises(ValidationError):
        MLModelCreate(
            name="x",
            version="1",
            task_type=TaskType.FEATURE_EXTRACTOR,
            embedding_dim=-1,
        )


def test_create_name_too_long_rejected():
    """max_length=200 on name is enforced."""
    with pytest.raises(ValidationError):
        MLModelCreate(
            name="x" * 201,
            version="1",
            task_type=TaskType.CLASSIFIER,
        )


def test_create_empty_name_rejected():
    """min_length=1 on name is enforced."""
    with pytest.raises(ValidationError):
        MLModelCreate(
            name="",
            version="1",
            task_type=TaskType.CLASSIFIER,
        )


# ----------------------------------------------------------------------
# MLModelUpdate — identity fields are absent (immutable)
# ----------------------------------------------------------------------


def test_update_has_no_identity_fields():
    """name, version, task_type cannot be patched — they belong to identity."""
    fields = MLModelUpdate.model_fields
    assert "name" not in fields
    assert "version" not in fields
    assert "task_type" not in fields


def test_update_accepts_partial_patch():
    """All fields optional; PATCH with only description works."""
    u = MLModelUpdate(description="Updated notes")
    assert u.description == "Updated notes"
    assert u.license is None


# ----------------------------------------------------------------------
# MLModelOut — computed fields + from_attributes
# ----------------------------------------------------------------------


class _ORMStub:
    """Minimal ORM-shaped object for MLModelOut.from_attributes."""

    def __init__(self, **kw):
        defaults = {
            "id": uuid4(),
            "tenant_id": "default",
            "name": "phikon-v2",
            "version": "2026.05",
            "framework": "pytorch",
            "architecture": "ViT-B",
            "task_type": "feature_extractor",
            "input_shape": {"h": 224, "w": 224, "c": 3},
            "embedding_dim": 768,
            "checkpoint_hash": None,
            "checkpoint_uri": None,
            "mlflow_run_id": None,
            "mlflow_experiment_id": None,
            "mlflow_model_uri": None,
            "license": "cc-by-nc-nd-4.0",
            "usage_constraints": None,
            "description": None,
            "metadata_extra": None,
            "registered_by": "admin@varuna-dev.local",
            "registered_at": datetime.now(UTC),
            "deployed_at": None,
            "retired_at": None,
            "updated_at": datetime.now(UTC),
        }
        defaults.update(kw)
        for k, v in defaults.items():
            setattr(self, k, v)


def test_out_from_orm_active_not_deployed():
    """Freshly registered model is active but not deployed."""
    obj = _ORMStub()
    out = MLModelOut.model_validate(obj)
    assert out.is_active is True
    assert out.is_deployed is False


def test_out_from_orm_deployed():
    """A model with deployed_at set and no retired_at is deployed."""
    obj = _ORMStub(deployed_at=datetime.now(UTC))
    out = MLModelOut.model_validate(obj)
    assert out.is_deployed is True
    assert out.is_active is True


def test_out_from_orm_retired_no_longer_active():
    """Retired model: not active, not deployed (even if it was)."""
    now = datetime.now(UTC)
    obj = _ORMStub(deployed_at=now - timedelta(days=30), retired_at=now)
    out = MLModelOut.model_validate(obj)
    assert out.is_active is False
    assert out.is_deployed is False


def test_out_commercial_use_for_apache():
    """apache-2.0 → commercial use allowed."""
    obj = _ORMStub(license="apache-2.0")
    out = MLModelOut.model_validate(obj)
    assert out.commercial_use_allowed is True
    assert out.open_source is True


def test_out_commercial_use_for_cc_nc():
    """cc-by-nc-nd-4.0 → commercial use NOT allowed, but open source."""
    obj = _ORMStub(license="cc-by-nc-nd-4.0")
    out = MLModelOut.model_validate(obj)
    assert out.commercial_use_allowed is False
    assert out.open_source is True


def test_out_commercial_use_for_proprietary():
    """proprietary → not open source, commercial use indeterminate via license."""
    obj = _ORMStub(license="proprietary")
    out = MLModelOut.model_validate(obj)
    assert out.open_source is False


def test_out_commercial_use_for_other_is_none():
    """OTHER license → both fields return None (manual review needed)."""
    obj = _ORMStub(license="other", description="custom")
    out = MLModelOut.model_validate(obj)
    assert out.commercial_use_allowed is None
    assert out.open_source is None


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def test_helpers_for_unset_license():
    """Both helpers return None when license is unknown."""
    assert is_commercial_use_allowed_for(None) is None
    assert is_open_source(None) is None
