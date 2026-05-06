"""
In-process MLWorkerProvider — runs inference directly in the FastAPI
event loop via an injected MLProvider.

When to use this backend
------------------------
- ONNX Runtime: releases the GIL during native ops, so Python can serve
  other requests during inference. No need for process isolation.
- OpenVINO: same — Intel's Python wrappers release the GIL.
- Lightweight model (<500 MB): the per-process loading cost (5-10s) is
  not worth amortising when the inference itself is sub-second.

When NOT to use
---------------
- Slideflow / PyTorch with full Python-level loops: bad GIL behaviour
  blocks the event loop. Use MLWorkerProxy (subprocess) instead.
- Memory-heavy models that must be isolated from the FastAPI process
  (e.g. crash on OOM should not bring down the API).

Design
------
- Lazy import of the underlying MLProvider (ML_PROVIDER env var) so
  importing this module doesn't pull in heavy ML deps unless the worker
  is actually selected at runtime.
- Submissions are dispatched via reflection: `await provider.<method>(*args, **kwargs)`.
  This matches MLWorkerProxy's submit() shape exactly.
- A single asyncio.Lock serialises submissions so callers see the same
  "one job at a time" behaviour as the subprocess worker. Callers that
  want concurrency should layer it on top.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional

from core.exceptions.ml_exceptions import MLProviderError

if TYPE_CHECKING:
    from core.interfaces.ml_provider import MLProvider

logger = logging.getLogger(__name__)


class InProcessMLWorker:
    """MLWorkerProvider implementer that runs inference in the calling loop.

    Wraps an MLProvider (Slideflow / Mock / ONNX / OpenVINO) and exposes
    the MLWorkerProvider Protocol surface. No subprocess, no IPC.
    """

    def __init__(self, provider: Optional["MLProvider"] = None) -> None:
        self._provider = provider
        self._started = False
        self._busy = False
        self._lock = asyncio.Lock()
        self._current_task: Optional[asyncio.Task] = None

    def _ensure_provider(self) -> "MLProvider":
        """Lazily resolve the MLProvider. Raises if no backend is available."""
        if self._provider is not None:
            return self._provider
        from core.interfaces import get_provider

        self._provider = get_provider()
        return self._provider

    # -- MLWorkerProvider Protocol ------------------------------------------

    async def submit(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Dispatch the call to `provider.<method>(*args, **kwargs)`.

        Acquires the worker lock so submissions are serialised (matching
        the subprocess worker's queue semantics). Wraps unexpected errors
        in MLProviderError to honour the worker contract.
        """
        if not self._started:
            self.start()

        async with self._lock:
            self._busy = True
            try:
                provider = self._ensure_provider()
                fn = getattr(provider, method, None)
                if fn is None:
                    raise MLProviderError(  # noqa: TRY301 — explicit shape mismatch, no value in extracting helper
                        f"Provider {type(provider).__name__} has no method {method!r}",
                        provider=type(provider).__name__,
                    )

                result = fn(*args, **kwargs)
                # Provider methods may be sync or async — handle both.
                if asyncio.iscoroutine(result):
                    self._current_task = asyncio.current_task()
                    try:
                        return await result
                    finally:
                        self._current_task = None
                return result
            except MLProviderError:
                raise
            except Exception as e:
                logger.exception(
                    "InProcessMLWorker submit(%s) failed unexpectedly", method
                )
                raise MLProviderError(
                    f"Unexpected error in InProcessMLWorker: {e}",
                    provider=type(self._provider).__name__ if self._provider else "unknown",
                    details={"method": method, "error": str(e)},
                ) from e
            finally:
                self._busy = False

    def start(self) -> None:
        """Mark the worker as ready. No process to spawn — just lazy init."""
        self._started = True

    def stop(self) -> None:
        """Drop the provider reference. Pending tasks (if any) will be
        cancelled by their own loop — we don't have direct control here.
        """
        self._started = False
        self._provider = None

    def restart(self) -> None:
        """Re-initialise the provider (forces a fresh ML_PROVIDER lookup)."""
        self.stop()
        self.start()

    def cancel_current(self) -> bool:
        """Cancel the currently-running task if any.

        InProcessMLWorker can leverage asyncio task cancellation when the
        provider method is async. For sync providers there's no clean
        cancellation point; the call must run to completion.
        """
        if self._current_task is None or self._current_task.done():
            return False
        self._current_task.cancel()
        return True

    def is_alive(self) -> bool:
        """In-process worker is always 'alive' once started — the FastAPI
        process IS the worker process."""
        return self._started

    def is_busy(self) -> bool:
        return self._busy


__all__ = ["InProcessMLWorker"]
