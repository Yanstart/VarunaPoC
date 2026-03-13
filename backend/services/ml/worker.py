"""
ML Worker Process - Isolated inference in a separate process.

Architecture:
    FastAPI (main)       multiprocessing       ML Worker (fork)
    port 8000        -->  Queue (jobs)    -->  loads model once
    serves tiles     <--  Queue (results) <--  1 job at a time
    stays light                                ~5 GB isolated

The worker is a multiprocessing.Process daemon:
- Loads the model ONCE at startup
- Processes jobs sequentially (no semaphore needed)
- Auto-restarts on crash
- Memory isolated from the main process
- Communication via multiprocessing.Queue (IPC, no external serialization)

References:
- Python multiprocessing: https://docs.python.org/3/library/multiprocessing.html
- FastAPI concurrency: https://fastapi.tiangolo.com/async/
"""

import logging
import multiprocessing
import os
import time
import traceback
import uuid
from concurrent.futures import Future
from dataclasses import dataclass, field
from threading import Thread
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

ML_TIMEOUT_SECONDS = int(os.getenv("ML_TIMEOUT_SECONDS", "120"))


@dataclass
class MLJob:
    """A job submitted to the ML worker."""

    job_id: str
    method: str
    args: Tuple = ()
    kwargs: Dict = field(default_factory=dict)


@dataclass
class MLResult:
    """Result returned by the ML worker."""

    job_id: str
    success: bool
    value: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None


class MLWorkerProxy:
    """
    Proxy on the main server process. Submits jobs to the worker.

    Usage:
        worker = MLWorkerProxy()
        worker.start()
        result = await worker.submit("predict", slide_path, region=None)
    """

    def __init__(self):
        self._process: Optional[multiprocessing.Process] = None
        self._job_queue: Optional[multiprocessing.Queue] = None
        self._result_queue: Optional[multiprocessing.Queue] = None
        self._pending: Dict[str, Future] = {}
        self._collector_thread: Optional[Thread] = None
        self._running = False
        self._last_submit_time: float = 0.0

    def start(self):
        """Spawn the worker process."""
        import atexit

        if self._process and self._process.is_alive():
            return

        self._job_queue = multiprocessing.Queue(maxsize=1)
        self._result_queue = multiprocessing.Queue()
        self._running = True

        # daemon=False: Slideflow spawns multiprocessing.Pool internally
        # for tile extraction. Python forbids daemon processes from having
        # children, so we use non-daemon + atexit cleanup instead.
        self._process = multiprocessing.Process(
            target=_worker_main,
            args=(self._job_queue, self._result_queue),
            daemon=False,
            name="ml-worker",
        )
        self._process.start()
        atexit.register(self.stop)
        logger.info("ML worker started (pid=%d)", self._process.pid)

        # Start result collector thread
        self._collector_thread = Thread(
            target=self._collect_results, daemon=True, name="ml-result-collector"
        )
        self._collector_thread.start()

    def is_alive(self) -> bool:
        """Check if the worker process is running."""
        return self._process is not None and self._process.is_alive()

    def is_busy(self) -> bool:
        """Check if the worker is currently processing a job.

        Includes staleness protection: if a job has been pending for longer
        than 2x the timeout, it is considered stale and the worker is
        auto-restarted to clear the deadlock.
        """
        if len(self._pending) == 0:
            return False

        stale_threshold = ML_TIMEOUT_SECONDS * 2
        if self._last_submit_time and (time.monotonic() - self._last_submit_time > stale_threshold):
            logger.warning(
                "Stale pending job detected (>%ds), auto-restarting worker",
                stale_threshold,
            )
            self.restart()
            return False

        return True

    def cancel_current(self):
        """Cancel the current job by restarting the worker process.

        Slideflow's internal multiprocessing.Pool cannot be interrupted
        gracefully, so the only reliable way to cancel is to kill the
        worker process and respawn it.
        """
        if not self.is_busy():
            return False
        logger.warning("Cancelling current ML job via worker restart")
        self.restart()
        return True

    def restart(self):
        """Kill and respawn the worker if it crashed."""
        logger.warning("Restarting ML worker...")
        self.stop()
        self.start()

    def stop(self):
        """Stop the worker process."""
        self._running = False

        if self._process and self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.kill()
                self._process.join(timeout=2)

        # Fail all pending futures
        for _job_id, future in self._pending.items():
            if not future.done():
                future.set_exception(RuntimeError("ML worker stopped while job was pending"))
        self._pending.clear()
        self._process = None
        logger.info("ML worker stopped")

    def _ensure_alive(self):
        """Auto-restart the worker if it crashed."""
        if not self.is_alive():
            logger.warning("ML worker is dead, auto-restarting...")
            self.restart()

    async def submit(self, method: str, *args, **kwargs) -> Any:
        """
        Submit a job to the ML worker and await the result.

        Args:
            method: Provider method name ("predict", "generate_heatmap", etc.)
            *args, **kwargs: Arguments passed to the provider method.

        Returns:
            The result from the provider method.

        Raises:
            MLWorkerBusyError: If the worker is already processing a job.
            MLWorkerTimeoutError: If the job exceeds the timeout.
            MLWorkerDownError: If the worker is down and cannot restart.
            Exception: Re-raised from the worker process.
        """
        import asyncio

        self._ensure_alive()

        if self.is_busy():
            raise MLWorkerBusyError("Le moteur d'inference est occupe.")

        job_id = str(uuid.uuid4())
        job = MLJob(job_id=job_id, method=method, args=args, kwargs=kwargs)

        future: Future = Future()
        self._pending[job_id] = future
        self._last_submit_time = time.monotonic()

        try:
            self._job_queue.put(job, timeout=5)
        except Exception:
            self._pending.pop(job_id, None)
            raise MLWorkerDownError("Cannot submit job to ML worker.")

        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, future.result),
                timeout=ML_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            self._pending.pop(job_id, None)
            # Worker process is stuck — restart it so the next job can proceed
            logger.warning(
                "Job %s timed out after %ds, restarting worker", job_id, ML_TIMEOUT_SECONDS
            )
            self.restart()
            minutes = ML_TIMEOUT_SECONDS // 60
            label = f"{minutes} min" if minutes >= 1 else f"{ML_TIMEOUT_SECONDS}s"
            raise MLWorkerTimeoutError(f"L'analyse a pris trop de temps (>{label}).")

    def _collect_results(self):
        """Background thread that collects results from the worker."""
        while self._running:
            try:
                result: MLResult = self._result_queue.get(timeout=1.0)
            except Exception:
                continue

            future = self._pending.pop(result.job_id, None)
            if future is None:
                continue

            if result.success:
                future.set_result(result.value)
            else:
                exc = MLWorkerExecutionError(
                    result.error or "Unknown worker error",
                    error_type=result.error_type,
                )
                future.set_exception(exc)


# ---------------------------------------------------------------------------
# Worker process entry point (runs in child process)
# ---------------------------------------------------------------------------


def _worker_main(job_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue):
    """
    Main loop running in the child process.

    Loads the ML provider once, then processes jobs sequentially.
    """
    import signal

    # Ignore SIGINT in worker — let parent handle it
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    _setup_worker_logging()

    worker_logger = logging.getLogger("ml_worker")
    worker_logger.info("ML worker process started (pid=%d)", os.getpid())

    provider = None
    services = {}  # Lazy-initialized service registry

    while True:
        try:
            job: MLJob = job_queue.get()
        except (EOFError, OSError):
            worker_logger.info("Job queue closed, worker exiting")
            break

        try:
            # Lazy-load provider on first job
            if provider is None:
                provider = _init_provider(worker_logger)
                services = _init_services(provider, worker_logger)

            # Look up method: provider first, then service registry
            method = getattr(provider, job.method, None) or services.get(job.method)
            if method is None:
                result_queue.put(
                    MLResult(
                        job_id=job.job_id,
                        success=False,
                        error=f"Unknown method: {job.method}",
                        error_type="AttributeError",
                    )
                )
                continue

            worker_logger.info("Processing job %s: %s", job.job_id[:8], job.method)
            start = time.monotonic()
            value = method(*job.args, **job.kwargs)
            elapsed = (time.monotonic() - start) * 1000
            worker_logger.info("Job %s completed in %.0f ms", job.job_id[:8], elapsed)

            result_queue.put(MLResult(job_id=job.job_id, success=True, value=value))

        except Exception as e:
            worker_logger.error("Job %s failed: %s", job.job_id[:8], e)
            result_queue.put(
                MLResult(
                    job_id=job.job_id,
                    success=False,
                    error=str(e),
                    error_type=type(e).__name__,
                )
            )


def _init_provider(worker_logger):
    """Initialize the ML provider inside the worker process."""
    from core.interfaces import get_provider

    provider_name = os.getenv("ML_PROVIDER", "slideflow")
    ml_mode = os.getenv("ML_MODE", "extractor")
    extractor_name = os.getenv("ML_EXTRACTOR", "resnet50_imagenet")
    model_path = os.getenv("ML_MODEL_PATH", "")

    worker_logger.info(
        "Initializing ML provider: %s (mode=%s, extractor=%s)",
        provider_name,
        ml_mode,
        extractor_name,
    )

    provider = get_provider(provider_name)

    if provider_name == "slideflow" and not provider.model_loaded:
        classes_str = os.getenv("ML_CLASSES", "tissue,background")
        classes = [c.strip() for c in classes_str.split(",") if c.strip()]

        if ml_mode == "classifier" and model_path:
            provider.load_model(
                model_path,
                {
                    "model_id": os.getenv("ML_MODEL_ID", "custom_classifier"),
                    "mode": "classifier",
                    "classes": classes,
                    "tile_size": int(os.getenv("ML_TILE_SIZE", "224")),
                    "num_mc_samples": int(os.getenv("ML_MC_SAMPLES", "10")),
                },
            )
        else:
            provider.load_model(
                f"extractor://{extractor_name}",
                {
                    "model_id": f"{extractor_name}_features",
                    "mode": "extractor",
                    "classes": classes,
                },
            )

    worker_logger.info("ML provider ready: %s", provider_name)
    return provider


def _init_services(provider, worker_logger):
    """Build a service registry for operations beyond raw provider methods.

    These wrap CellCountingService, ClusteringService, QualityService so they
    can be dispatched through the worker queue just like provider methods.
    """
    from services.cache.disk_cache import DiskCache
    from services.ml.clustering import ClusteringService
    from services.ml.counting import CellCountingService
    from services.ml.quality import QualityService

    disk_cache = DiskCache()
    model_id = (
        provider.model_config.get("model_id", "unknown")
        if getattr(provider, "model_loaded", False)
        else "unknown"
    )

    counting_svc = CellCountingService()
    clustering_svc = ClusteringService()
    quality_svc = QualityService()

    def _count(
        slide_path,
        stain="Ki67",
        region=None,
        include_positions=False,
        slide_dimensions=None,
    ):
        return counting_svc.count_cells(
            slide_path=slide_path,
            provider=provider,
            stain=stain,
            region=region,
            include_positions=include_positions,
            slide_dimensions=slide_dimensions,
        )

    registry = {
        "count_cells": _count,
        "cluster": lambda slide_path, n_clusters=4: clustering_svc.cluster(
            slide_path=slide_path,
            n_clusters=n_clusters,
            disk_cache=disk_cache,
            model_id=model_id,
        ),
        "assess_quality": lambda slide_path: quality_svc.assess_quality(
            slide_path=slide_path,
            disk_cache=disk_cache,
            model_id=model_id,
        ),
    }

    worker_logger.info("Service registry initialized: %s", list(registry.keys()))
    return registry


def _setup_worker_logging():
    """Configure logging for the worker process."""
    logging.basicConfig(
        level=logging.INFO,
        format="[ML Worker %(process)d] %(levelname)s %(name)s: %(message)s",
    )


# ---------------------------------------------------------------------------
# Worker-specific exceptions
# ---------------------------------------------------------------------------


class MLWorkerError(Exception):
    """Base exception for ML worker errors."""


class MLWorkerBusyError(MLWorkerError):
    """Raised when the worker is already processing a job."""


class MLWorkerTimeoutError(MLWorkerError):
    """Raised when a job exceeds the timeout."""


class MLWorkerDownError(MLWorkerError):
    """Raised when the worker process is down."""


class MLWorkerExecutionError(MLWorkerError):
    """Raised when the worker encounters an error during job execution."""

    def __init__(self, message: str, error_type: str = ""):
        self.error_type = error_type
        super().__init__(message)
