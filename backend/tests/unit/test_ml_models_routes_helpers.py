"""Unit tests for the pure helpers in `backend/routes/ml_models.py`.

Covers:
  - `_safe_model_out`: graceful fallback when the DB row carries a license
    value that is not in the Pydantic `License` enum.
  - `_validate_patch_merged_state`: re-runs Create-side invariants on the
    would-be post-PATCH state. Identity fields and unchanged fields are
    drawn from the existing ORM row; patched fields override.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from routes.ml_models import _safe_model_out, _validate_patch_merged_state


class _MLModelStub:
    """Minimal duck-typed stand-in for the SQLAlchemy `MLModel` ORM row."""

    def __init__(self, **overrides):
        defaults = {
            "id": uuid4(),
            "tenant_id": "default",
            "name": "stub-classifier",
            "version": "1.0.0",
            "framework": "pytorch",
            "architecture": "ResNet50",
            "task_type": "classifier",
            "input_shape": None,
            "embedding_dim": None,
            "checkpoint_hash": None,
            "checkpoint_uri": None,
            "mlflow_run_id": None,
            "mlflow_experiment_id": None,
            "mlflow_model_uri": None,
            "license": "apache-2.0",
            "usage_constraints": None,
            "description": None,
            "metadata_extra": None,
            "registered_by": "tester@varuna-dev.local",
            "registered_at": datetime.now(UTC),
            "deployed_at": None,
            "retired_at": None,
            "updated_at": datetime.now(UTC),
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# _safe_model_out
# ---------------------------------------------------------------------------


def test_safe_model_out_happy_path_returns_normal_validation():
    obj = _MLModelStub(license="apache-2.0")
    out = _safe_model_out(obj)
    assert out.license.value == "apache-2.0"
    # metadata_extra was None and stays None — no fallback was needed
    assert out.metadata_extra is None


def test_safe_model_out_unknown_license_falls_back_to_none():
    """An out-of-enum license must NOT 500 — it surfaces as license=None
    with the raw value preserved in metadata_extra.license_raw."""
    obj = _MLModelStub(license="frankenstein-1.0")
    out = _safe_model_out(obj)
    assert out.license is None
    assert out.metadata_extra == {"license_raw": "frankenstein-1.0"}
    # The rest of the model still round-trips correctly
    assert out.name == "stub-classifier"
    assert out.tenant_id == "default"


def test_safe_model_out_unknown_license_preserves_existing_metadata_extra():
    """When the row already has metadata_extra, the fallback must merge,
    not clobber. license_raw is added alongside existing keys."""
    obj = _MLModelStub(
        license="frankenstein-1.0",
        metadata_extra={"source": "huggingface", "tags": ["histology"]},
    )
    out = _safe_model_out(obj)
    assert out.metadata_extra["source"] == "huggingface"
    assert out.metadata_extra["tags"] == ["histology"]
    assert out.metadata_extra["license_raw"] == "frankenstein-1.0"


def test_safe_model_out_unknown_license_does_not_override_existing_license_raw():
    """If `license_raw` already exists in metadata_extra, the fallback
    `setdefault` semantic preserves the existing key."""
    obj = _MLModelStub(
        license="frankenstein-1.0",
        metadata_extra={"license_raw": "previously-known-bad-value"},
    )
    out = _safe_model_out(obj)
    assert out.metadata_extra["license_raw"] == "previously-known-bad-value"


# ---------------------------------------------------------------------------
# _validate_patch_merged_state
# ---------------------------------------------------------------------------


def test_validate_patch_passes_on_safe_changes():
    obj = _MLModelStub(task_type="classifier", license="apache-2.0")
    # Only changing the description — Create invariants are satisfied
    _validate_patch_merged_state(obj, {"description": "Updated"})


def test_validate_patch_rejects_license_other_without_description():
    """PATCH that turns the license into OTHER without supplying a
    description must be rejected with 422 (Create invariant)."""
    obj = _MLModelStub(task_type="classifier", license="apache-2.0", description=None)
    with pytest.raises(HTTPException) as exc_info:
        _validate_patch_merged_state(obj, {"license": "other"})
    assert exc_info.value.status_code == 422
    detail = exc_info.value.detail
    assert "invalid state" in detail["message"].lower()


def test_validate_patch_accepts_license_other_with_description_in_same_patch():
    """If the PATCH supplies BOTH license=other AND description, it must
    pass — the merge sees both fields set."""
    obj = _MLModelStub(task_type="classifier", license="apache-2.0", description=None)
    _validate_patch_merged_state(
        obj,
        {"license": "other", "description": "Custom in-house clause"},
    )


def test_validate_patch_accepts_license_other_when_row_already_has_description():
    """The merged dict draws description from the existing row when the
    patch does not touch it. Existing description must satisfy the
    license=OTHER rule."""
    obj = _MLModelStub(
        task_type="classifier",
        license="apache-2.0",
        description="Already documented",
    )
    _validate_patch_merged_state(obj, {"license": "other"})


def test_validate_patch_rejects_extractor_losing_embedding_dim():
    """An extractor row cannot have its embedding_dim PATCH-set to None —
    Create invariant 'feature_extractor requires embedding_dim'."""
    obj = _MLModelStub(task_type="feature_extractor", embedding_dim=768)
    with pytest.raises(HTTPException) as exc_info:
        _validate_patch_merged_state(obj, {"embedding_dim": None})
    assert exc_info.value.status_code == 422
