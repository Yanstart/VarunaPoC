"""
Triton Inference Server MLWorkerProvider — stub for the remote-inference
backend.

Why this is a stub today
------------------------
- VarunaPoC has no Triton server deployment yet (CHU UCL Namur runs ML
  inference on the same host as the API today).
- The Triton client API (HTTP / gRPC, model management, ensemble pipelines,
  GPU placement) is non-trivial — implementing it without a target server
  to validate against would be guesswork.

What this stub does
-------------------
- Defines the class shape so the factory `get_ml_worker_provider()` can
  resolve `ML_WORKER_BACKEND=triton` to a concrete (if non-functional)
  implementation, with a clear error message.
- Documents the migration path: env vars (TRITON_URL, TRITON_MODEL_NAME,
  TRITON_PROTOCOL=http|grpc), the `tritonclient` Python package, and the
  mapping of MLWorkerProvider methods to Triton inference calls.

When ready to implement, replace each NotImplementedError with the
real client call. The Protocol contract (MLWorkerProvider) is the
single specification — nothing else in the codebase needs to change.

References:
- Triton: https://github.com/triton-inference-server/server
- tritonclient: https://github.com/triton-inference-server/client
- KServe (Kubernetes): https://kserve.github.io/website/
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TritonClientMLWorker:
    """Stub MLWorkerProvider for a remote Triton Inference Server.

    Configuration (read at instantiation):
    - TRITON_URL              (default http://localhost:8000)
    - TRITON_PROTOCOL         http | grpc (default http)
    - TRITON_MODEL_NAME       e.g. "varuna_pathology"
    - TRITON_MODEL_VERSION    e.g. "1" (empty → latest)
    - TRITON_TIMEOUT_SECONDS  (default 60)
    """

    def __init__(self, url: Optional[str] = None) -> None:
        self._url = url or os.getenv("TRITON_URL", "http://localhost:8000")
        self._protocol = os.getenv("TRITON_PROTOCOL", "http").lower()
        self._model_name = os.getenv("TRITON_MODEL_NAME", "")
        self._model_version = os.getenv("TRITON_MODEL_VERSION", "")
        self._timeout = float(os.getenv("TRITON_TIMEOUT_SECONDS", "60"))
        self._client = None  # tritonclient instance, lazily created
        self._started = False

    # -- MLWorkerProvider Protocol ------------------------------------------

    async def submit(self, method: str, *args: Any, **kwargs: Any) -> Any:
        msg = (
            f"TritonClientMLWorker.submit({method!r}) is not implemented. "
            f"Configure ML_WORKER_BACKEND=subprocess|inprocess until a Triton "
            f"server is available, or implement this method by replacing the "
            f"stub with a tritonclient.http.InferenceServerClient.infer() call."
        )
        raise NotImplementedError(msg)

    def start(self) -> None:
        """Establish the Triton client connection.

        Today: just sets _started=True so is_alive() can be honest about
        the configuration phase. Real impl: instantiate
        `tritonclient.http.InferenceServerClient(url=self._url)`,
        ping `/v2/health/ready`, raise on failure.
        """
        if not self._model_name:
            logger.warning(
                "TritonClientMLWorker started without TRITON_MODEL_NAME — "
                "submissions will fail until configured."
            )
        self._started = True

    def stop(self) -> None:
        """Close the Triton client (HTTP session / gRPC channel)."""
        self._client = None
        self._started = False

    def restart(self) -> None:
        self.stop()
        self.start()

    def cancel_current(self) -> bool:
        """Cancel an in-flight HTTP/gRPC request.

        Real impl: cancel the asyncio task wrapping the tritonclient call.
        Today we have no in-flight requests since submit() raises immediately.
        """
        return False

    def is_alive(self) -> bool:
        """Configuration check.

        Real impl should also ping Triton's /v2/health/ready and report
        False on connection failure.
        """
        return self._started and bool(self._model_name)

    def is_busy(self) -> bool:
        return False


__all__ = ["TritonClientMLWorker"]
