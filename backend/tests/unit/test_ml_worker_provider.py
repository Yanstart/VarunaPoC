"""Sprint 11 — verifies the MLWorkerProvider Protocol is satisfied by all
3 implementers (subprocess / in-process / Triton stub) and that the
factory selects the right one based on env config.

The MLWorkerProxy subprocess test is light-touch: we don't actually spawn
the Slideflow worker (that requires the full ML stack and ~5GB RAM).
We just check the class shape via isinstance() and `is_alive()`.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.exceptions.ml_exceptions import MLProviderError
from core.interfaces import MLWorkerProvider
from services.ml import get_ml_worker_provider, reset_ml_worker_provider
from services.ml.inprocess_worker import InProcessMLWorker
from services.ml.triton_worker import TritonClientMLWorker

# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_inprocess_worker_satisfies_protocol():
    assert isinstance(InProcessMLWorker(), MLWorkerProvider)


def test_triton_worker_satisfies_protocol():
    assert isinstance(TritonClientMLWorker(), MLWorkerProvider)


def test_subprocess_worker_satisfies_protocol():
    """The legacy MLWorkerProxy must structurally satisfy the new Protocol
    so it can be picked by the factory without code changes."""
    from services.ml.worker import MLWorkerProxy

    assert isinstance(MLWorkerProxy(), MLWorkerProvider)


# ---------------------------------------------------------------------------
# Factory selection
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Each test starts with a fresh factory state."""
    reset_ml_worker_provider()
    yield
    reset_ml_worker_provider()


def test_factory_default_is_subprocess(monkeypatch):
    monkeypatch.delenv("ML_WORKER_BACKEND", raising=False)
    from services.ml.worker import MLWorkerProxy

    worker = get_ml_worker_provider()
    assert isinstance(worker, MLWorkerProxy)


def test_factory_returns_inprocess_when_configured(monkeypatch):
    monkeypatch.setenv("ML_WORKER_BACKEND", "inprocess")
    worker = get_ml_worker_provider()
    assert isinstance(worker, InProcessMLWorker)


def test_factory_returns_triton_when_configured(monkeypatch):
    monkeypatch.setenv("ML_WORKER_BACKEND", "triton")
    worker = get_ml_worker_provider()
    assert isinstance(worker, TritonClientMLWorker)


def test_factory_falls_back_to_subprocess_on_unknown_backend(monkeypatch):
    monkeypatch.setenv("ML_WORKER_BACKEND", "magic_unicorn")
    from services.ml.worker import MLWorkerProxy

    worker = get_ml_worker_provider()
    assert isinstance(worker, MLWorkerProxy)


def test_factory_returns_singleton(monkeypatch):
    monkeypatch.setenv("ML_WORKER_BACKEND", "inprocess")
    a = get_ml_worker_provider()
    b = get_ml_worker_provider()
    assert a is b


# ---------------------------------------------------------------------------
# InProcessMLWorker behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inprocess_submit_dispatches_to_provider_method():
    """submit('predict', slide_path) → provider.predict(slide_path)."""
    fake_provider = MagicMock()
    fake_provider.predict = AsyncMock(return_value={"prediction": "tumor"})

    worker = InProcessMLWorker(provider=fake_provider)
    result = await worker.submit("predict", "/slides/foo.svs")

    assert result == {"prediction": "tumor"}
    fake_provider.predict.assert_awaited_once_with("/slides/foo.svs")


@pytest.mark.asyncio
async def test_inprocess_submit_handles_sync_provider_method():
    """Sync provider methods are returned directly (not awaited)."""
    fake_provider = MagicMock()
    fake_provider.extract_features = MagicMock(return_value={"shape": [10, 768]})

    worker = InProcessMLWorker(provider=fake_provider)
    result = await worker.submit("extract_features", "/slides/foo.svs")

    assert result == {"shape": [10, 768]}


@pytest.mark.asyncio
async def test_inprocess_submit_raises_ml_provider_error_for_unknown_method():
    fake_provider = MagicMock(spec=["predict"])  # only `predict` exists
    worker = InProcessMLWorker(provider=fake_provider)
    with pytest.raises(MLProviderError) as exc:
        await worker.submit("nonexistent_method", "/slides/foo.svs")
    assert "nonexistent_method" in str(exc.value)


@pytest.mark.asyncio
async def test_inprocess_submit_wraps_unexpected_exceptions():
    fake_provider = MagicMock()
    fake_provider.predict = AsyncMock(side_effect=RuntimeError("model crashed"))
    worker = InProcessMLWorker(provider=fake_provider)
    with pytest.raises(MLProviderError) as exc:
        await worker.submit("predict", "/slides/foo.svs")
    assert "model crashed" in str(exc.value)


@pytest.mark.asyncio
async def test_inprocess_submit_passes_through_ml_provider_errors():
    """Existing MLProviderError instances (from the provider) must NOT be
    re-wrapped — the route layer relies on the original exception type.
    """
    fake_provider = MagicMock()
    original = MLProviderError("explicit error", provider="test")
    fake_provider.predict = AsyncMock(side_effect=original)

    worker = InProcessMLWorker(provider=fake_provider)
    with pytest.raises(MLProviderError) as exc:
        await worker.submit("predict", "/slides/foo.svs")
    assert exc.value is original


def test_inprocess_lifecycle_methods():
    worker = InProcessMLWorker()
    assert worker.is_alive() is False  # before start
    worker.start()
    assert worker.is_alive() is True
    assert worker.is_busy() is False
    worker.stop()
    assert worker.is_alive() is False
    # restart is start+stop
    worker.restart()
    assert worker.is_alive() is True


def test_inprocess_cancel_returns_false_when_idle():
    worker = InProcessMLWorker()
    worker.start()
    assert worker.cancel_current() is False


# ---------------------------------------------------------------------------
# TritonClientMLWorker stub behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_triton_submit_raises_not_implemented():
    """Until a real Triton deployment exists, submit() must fail loudly so
    misconfigured deployments don't silently no-op."""
    worker = TritonClientMLWorker()
    with pytest.raises(NotImplementedError) as exc:
        await worker.submit("predict", "/slides/foo.svs")
    # Error message must point to the alternative backends.
    assert "ML_WORKER_BACKEND" in str(exc.value)


def test_triton_lifecycle_does_not_raise_without_real_server(monkeypatch):
    """start/stop must work even without TRITON_MODEL_NAME (the stub
    just sets _started; real impl will ping /v2/health/ready and raise)."""
    monkeypatch.delenv("TRITON_MODEL_NAME", raising=False)
    worker = TritonClientMLWorker()
    worker.start()  # logs a warning but doesn't raise
    assert worker.is_alive() is False  # no model name → not alive
    worker.stop()


def test_triton_is_alive_when_configured(monkeypatch):
    monkeypatch.setenv("TRITON_MODEL_NAME", "varuna_pathology")
    monkeypatch.setenv("TRITON_URL", "http://triton.internal:8000")
    worker = TritonClientMLWorker()
    worker.start()
    assert worker.is_alive() is True
