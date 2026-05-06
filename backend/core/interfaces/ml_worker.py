"""
ML Worker Provider Interface

PURPOSE: Abstract the *execution backend* for ML inference, decoupled
from the inference contract itself (`MLProvider`).

Two layers, kept orthogonal:

- **`MLProvider`** (in `ml_provider.py`): WHAT inference can be requested
  (predict / extract_features / generate_heatmap, with structured results).
- **`MLWorkerProvider`** (this module): HOW that inference is executed —
  in a forked subprocess (today, for Slideflow), in-process (for ONNX
  Runtime or OpenVINO that release the GIL well), or remotely (Triton
  Inference Server, KServe, BentoML).

The route layer (`routes/ml.py`) submits jobs through the worker and
doesn't care which backend runs them. Switching backends is an env-var
flip (ML_WORKER_BACKEND=subprocess|inprocess|triton).

Implementations:
- `MLWorkerProxy` (services/ml/worker.py) — multiprocessing daemon with
  Slideflow loaded once. Today's default. Heavy (~5GB resident) but
  isolated from the FastAPI process.
- `InProcessMLWorker` (services/ml/inprocess_worker.py) — runs inference
  in the calling event loop via an injected `MLProvider`. Cheap; suitable
  for ONNX Runtime / OpenVINO that release the GIL during native ops.
- `TritonClientMLWorker` (services/ml/triton_worker.py) — HTTP/gRPC client
  to a remote Triton Inference Server. Stub today; documents the path to
  hospital-grade GPU inference farms.

References:
- ONNX Runtime: https://onnxruntime.ai/
- OpenVINO: https://docs.openvino.ai/
- Triton Inference Server: https://github.com/triton-inference-server/server
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MLWorkerProvider(Protocol):
    """Protocol for ML worker execution backends.

    Lifecycle:
        worker = SomeMLWorker(...)
        worker.start()                         # idempotent
        result = await worker.submit("predict", slide_path, region=None)
        worker.stop()                          # graceful shutdown

    Concurrency:
        Implementations MAY serialize submissions (e.g. MLWorkerProxy
        with maxsize=1 queue) or accept concurrent submissions
        (InProcessMLWorker for thread-safe providers). Callers should
        treat `submit` as sequential per worker instance.

    Cancellation:
        `cancel_current()` returns True if a job was running and was
        cancelled. The strategy is implementation-specific (process
        restart for subprocess workers, asyncio task cancellation for
        in-process workers, HTTP request cancellation for remote workers).
    """

    async def submit(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Submit a job and await its result.

        Args:
            method: Provider method name ("predict", "extract_features",
                    "generate_heatmap", etc.). Implementations route this
                    to the underlying inference engine.
            *args, **kwargs: Forwarded to the inference engine.

        Returns:
            The provider's typed result (PredictionResult, FeatureExtractionResult,
            HeatmapResult, etc.).

        Raises:
            MLProviderError or its subclasses on inference failure. Worker-
            level errors (timeout, crash, unavailable backend) raise
            MLWorkerError or its subclasses.
        """
        ...

    def start(self) -> None:
        """Start the worker (spawn process / connect to remote / no-op).

        Idempotent: calling start() on an already-running worker is a no-op.
        """
        ...

    def stop(self) -> None:
        """Stop the worker (terminate process / disconnect / no-op).

        After stop(), submit() raises until start() is called again.
        Pending submissions fail with MLWorkerDownError.
        """
        ...

    def restart(self) -> None:
        """Stop then start. Used to recover from a crashed worker."""
        ...

    def cancel_current(self) -> bool:
        """Cancel the currently-running job. Returns True if a job was cancelled."""
        ...

    def is_alive(self) -> bool:
        """Return True if the worker is healthy and ready to accept submissions."""
        ...

    def is_busy(self) -> bool:
        """Return True if the worker is currently processing a job."""
        ...


__all__ = ["MLWorkerProvider"]
