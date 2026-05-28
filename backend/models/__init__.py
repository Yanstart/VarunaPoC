"""ORM Models for VarunaPoC Phase 2 + Phase 3 Auth + Phase 4 Quality + Phase 5 Corrections + Phase 6 ML Registry."""

from .annotation import Annotation
from .annotation_label import AnnotationLabel
from .correction import Correction
from .ml_model import MLModel
from .view_history import ViewHistory
from .worklist import WorklistAssignment

# Phase 3: Auth models (optional - requires auth module)
try:
    from auth.models import AuditEvent, BreakGlassLog, SessionState, User

    _AUTH_MODELS = [User, AuditEvent, SessionState, BreakGlassLog]
except ImportError:
    _AUTH_MODELS = []

# Phase 4: Quality reports cache (optional)
try:
    from .quality_report import QualityReport

    _QUALITY_MODELS = [QualityReport]
except ImportError:
    _QUALITY_MODELS = []

__all__ = (
    [
        "Annotation",
        "AnnotationLabel",
        "Correction",
        "MLModel",
        "ViewHistory",
        "WorklistAssignment",
    ]
    + [m.__name__ for m in _AUTH_MODELS]
    + [m.__name__ for m in _QUALITY_MODELS]
)
