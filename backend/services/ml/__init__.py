"""
ML Services Package
Services pour MLOps et apprentissage continu.

Modules:
- tag_extractor: Extraction automatique tags (organ, stain, marker)
- tag_router: Routage intelligent vers modèles spécialisés
- model_inference: Inférence ML avec uncertainty quantification
- feedback_service: Capture feedback pathologistes
- dataset_builder: Construction datasets enrichis avec feedback
- retraining_monitor: Monitoring et déclenchement re-entraînement
- drift_detector: Détection drift données/prédictions
- worker: Subprocess-based MLWorkerProvider (default backend, Slideflow)
- inprocess_worker: In-process MLWorkerProvider for ONNX / OpenVINO
- triton_worker: Stub remote MLWorkerProvider (Triton Inference Server)

Référence: docs/MLOPS_ARCHITECTURE.md
"""

import logging
import os

logger = logging.getLogger(__name__)

# Lazy imports to avoid OpenSlide dependency issues
__all__ = [
    "TagExtractor",
    "TagRouter",
    "ModelRoute",
    "get_ml_worker_provider",
]


def __getattr__(name):
    """Lazy import to avoid loading OpenSlide at import time."""
    if name == "TagExtractor":
        from .tag_extractor import TagExtractor

        return TagExtractor
    elif name == "TagRouter":
        from .tag_router import TagRouter

        return TagRouter
    elif name == "ModelRoute":
        from .tag_router import ModelRoute

        return ModelRoute
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# ---------------------------------------------------------------------------
# MLWorkerProvider factory (sprint 11)
# ---------------------------------------------------------------------------

_worker_singleton = None


def get_ml_worker_provider():
    """Return the singleton MLWorkerProvider chosen by ML_WORKER_BACKEND.

    Backends:
    - "subprocess" (default) — MLWorkerProxy: fork a Slideflow worker process.
      Heavy (~5GB resident) but isolated. Keeps the FastAPI process light.
    - "inprocess"            — InProcessMLWorker: run ML directly in the
      event loop via the configured MLProvider. Cheap. Suitable for ONNX /
      OpenVINO that release the GIL during native ops. Avoid with Slideflow.
    - "triton"               — TritonClientMLWorker: HTTP/gRPC to a remote
      Triton Inference Server. Stub today (raises NotImplementedError on
      submit) but the env wiring exists so the route layer works once a
      Triton deployment is configured.

    The singleton is created lazily on first call. Tests can reset it via
    `reset_ml_worker_provider()` (below) for isolation between cases.
    """
    global _worker_singleton
    if _worker_singleton is not None:
        return _worker_singleton

    backend = os.getenv("ML_WORKER_BACKEND", "subprocess").strip().lower()
    if backend == "inprocess":
        from .inprocess_worker import InProcessMLWorker

        _worker_singleton = InProcessMLWorker()
    elif backend == "triton":
        from .triton_worker import TritonClientMLWorker

        _worker_singleton = TritonClientMLWorker()
    else:
        # Default: subprocess. Backward-compatible with the existing
        # MLWorkerProxy that ml.py uses today.
        if backend not in ("subprocess", ""):
            logger.warning(
                "Unknown ML_WORKER_BACKEND=%r, falling back to 'subprocess'",
                backend,
            )
        from .worker import MLWorkerProxy

        _worker_singleton = MLWorkerProxy()
    return _worker_singleton


def reset_ml_worker_provider() -> None:
    """Test helper: clear the singleton so the next call re-resolves the env."""
    global _worker_singleton
    if _worker_singleton is not None and hasattr(_worker_singleton, "stop"):
        import contextlib

        with contextlib.suppress(Exception):
            _worker_singleton.stop()
    _worker_singleton = None
