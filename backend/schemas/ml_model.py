"""ML Model registry schemas — Pydantic contracts for the ml_models API.

The DB lets `task_type` and `license` be free VARCHARs (design decision B
in #370) so adding a new value is a Python patch, not a migration. The
strict contracts live here at the API boundary.

Varuna is a 100% open source project — the License enum lists the OSI /
Creative Commons / Software Freedom licenses we encounter in foundation
models (UNI, CONCH, Virchow, GigaPath, Phikon-v2). `proprietary` is kept
as a valid value because the registry must be able to *trace* non-open
models for compliance audits, but the registered_by must explicitly tag
them.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, model_validator

# ============================================
# Enums (strict at the API boundary, free at the DB)
# ============================================


class TaskType(str, Enum):
    """ML task category. Maps directly to MLWorkerProvider routing."""

    FEATURE_EXTRACTOR = "feature_extractor"
    CLASSIFIER = "classifier"
    DETECTOR = "detector"
    SEGMENTER = "segmenter"


class License(str, Enum):
    """Licenses encountered in pathology foundation models + Varuna stack.

    Adding a new value is a Python patch (no DB migration) — the DB column
    is a free VARCHAR.

    Commercial use status is encoded in `is_commercial_use_allowed_for()`.
    """

    # OSI permissive
    APACHE_2_0 = "apache-2.0"
    MIT = "mit"
    BSD_2_CLAUSE = "bsd-2-clause"
    BSD_3_CLAUSE = "bsd-3-clause"
    MPL_2_0 = "mpl-2.0"

    # OSI copyleft
    GPL_2_0 = "gpl-2.0"
    GPL_3_0 = "gpl-3.0"
    LGPL_3_0 = "lgpl-3.0"
    AGPL_3_0 = "agpl-3.0"

    # Creative Commons — commercial OK
    CC_BY_4_0 = "cc-by-4.0"
    CC_BY_SA_4_0 = "cc-by-sa-4.0"
    CC0_1_0 = "cc0-1.0"

    # Creative Commons — non-commercial (UNI, CONCH …)
    CC_BY_NC_4_0 = "cc-by-nc-4.0"
    CC_BY_NC_ND_4_0 = "cc-by-nc-nd-4.0"

    # Hugging Face-specific (mSTAR …)
    OPENRAIL = "openrail"

    # Tracking-only — registry must be able to *see* non-open models for audit
    PROPRIETARY = "proprietary"
    OTHER = "other"


_NON_COMMERCIAL_LICENSES: frozenset[License] = frozenset(
    {License.CC_BY_NC_4_0, License.CC_BY_NC_ND_4_0}
)

_NON_OPEN_LICENSES: frozenset[License] = frozenset({License.PROPRIETARY, License.OTHER})


def is_commercial_use_allowed_for(license_value: License | None) -> bool | None:
    """Best-effort commercial-use flag.

    Returns None if the license is `OTHER` or unset (real answer requires
    reading the `description`). Caller must fall back to manual review.
    """
    if license_value is None or license_value == License.OTHER:
        return None
    return license_value not in _NON_COMMERCIAL_LICENSES


def is_open_source(license_value: License | None) -> bool | None:
    """True if the license is OSI / Creative Commons. None when uncertain."""
    if license_value is None or license_value == License.OTHER:
        return None
    return license_value not in _NON_OPEN_LICENSES


# ============================================
# Sub-models
# ============================================


class InputShape(BaseModel):
    """Expected input tensor shape for an ML model."""

    h: int = Field(gt=0, description="Tile height in pixels")
    w: int = Field(gt=0, description="Tile width in pixels")
    c: int = Field(gt=0, description="Number of channels (1=grayscale, 3=RGB, 4=RGBA)")


# ============================================
# Base + Create + Update + Out
# ============================================


class MLModelBase(BaseModel):
    """Shared fields between Create / Update / Out."""

    name: str = Field(..., min_length=1, max_length=200, description="Model name")
    version: str = Field(
        ..., min_length=1, max_length=50, description="Semver, hash, or free-form version tag"
    )
    framework: str | None = Field(
        None, max_length=50, description="pytorch, tensorflow, onnx, tflite, …"
    )
    architecture: str | None = Field(
        None, max_length=100, description="Free-form architecture descriptor"
    )
    task_type: TaskType
    input_shape: InputShape | None = None
    embedding_dim: int | None = Field(
        None, ge=0, description="Embedding dimensionality (extractors only)"
    )
    checkpoint_hash: str | None = Field(
        None, min_length=8, max_length=128, description="SHA-256 of the checkpoint"
    )
    checkpoint_uri: str | None = Field(None, description="s3://, hf://, local://, etc.")
    mlflow_run_id: str | None = Field(None, max_length=64)
    mlflow_experiment_id: str | None = Field(None, max_length=32)
    mlflow_model_uri: str | None = Field(
        None, description="MLflow URI: 'models:/<name>/<version>' or 'runs:/<run_id>/<artifact>'"
    )
    license: License | None = None
    usage_constraints: dict[str, Any] | None = Field(
        None,
        description="Optional structured constraints (e.g. {'commercial': false, 'phi': true})",
    )
    description: str | None = Field(None, description="Free-form description")
    metadata_extra: dict[str, Any] | None = Field(
        None, description="Arbitrary extension fields not yet promoted to columns"
    )


class MLModelCreate(MLModelBase):
    """Payload for POST /api/v1/ml-models.

    `tenant_id` is intentionally absent — the caller's tenant is always
    injected server-side from the authenticated context. To register a
    model shared across tenants (foundation models), call the dedicated
    POST /api/v1/ml-models/global endpoint (ADMIN_TECHNIQUE only).
    """

    @model_validator(mode="after")
    def require_description_when_license_other(self) -> "MLModelCreate":
        """OTHER license is the escape hatch — it must be documented."""
        if self.license == License.OTHER and not (self.description and self.description.strip()):
            msg = "license=OTHER requires a non-empty description"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def require_embedding_dim_for_extractors(self) -> "MLModelCreate":
        """Extractors are useless without a declared embedding dimensionality."""
        if self.task_type == TaskType.FEATURE_EXTRACTOR and self.embedding_dim is None:
            msg = "feature_extractor task_type requires embedding_dim"
            raise ValueError(msg)
        return self


class MLModelUpdate(BaseModel):
    """PATCH payload. Identity fields (name, version, task_type) are immutable.

    Changing identity = registering a new row, not patching the existing one.
    """

    framework: str | None = Field(None, max_length=50)
    architecture: str | None = Field(None, max_length=100)
    input_shape: InputShape | None = None
    embedding_dim: int | None = Field(None, ge=0)
    checkpoint_hash: str | None = Field(None, min_length=8, max_length=128)
    checkpoint_uri: str | None = None
    mlflow_run_id: str | None = Field(None, max_length=64)
    mlflow_experiment_id: str | None = Field(None, max_length=32)
    mlflow_model_uri: str | None = None
    license: License | None = None
    usage_constraints: dict[str, Any] | None = None
    description: str | None = None
    metadata_extra: dict[str, Any] | None = None


class MLModelOut(MLModelBase):
    """Response payload."""

    id: UUID
    tenant_id: str
    registered_by: str | None
    registered_at: datetime
    deployed_at: datetime | None
    retired_at: datetime | None
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        """True iff registered and not yet retired."""
        return self.retired_at is None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_deployed(self) -> bool:
        """True iff deployed and not yet retired."""
        return self.deployed_at is not None and self.retired_at is None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def commercial_use_allowed(self) -> bool | None:
        """Best-effort commercial-use status derived from the license."""
        return is_commercial_use_allowed_for(self.license)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def open_source(self) -> bool | None:
        """Best-effort open source status derived from the license."""
        return is_open_source(self.license)

    model_config = {"from_attributes": True}
