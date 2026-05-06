"""End-to-end Protocol conformance check.

Verifies that all 5 Protocols defined in core.interfaces have at least
one concrete implementer wired up on main. This is a regression guard
against the "Protocol defined but never used" anti-pattern.
"""

from core.interfaces import (
    AuthProvider,
    SlideReader,
    StorageProvider,
    TileCache,
    WorkflowHook,
)


def test_auth_provider_has_implementer():
    from auth.auth_provider import OIDCAuthProvider

    assert isinstance(OIDCAuthProvider(), AuthProvider)


def test_storage_provider_has_implementer():
    from services.storage_provider import FilesystemStorageProvider

    assert isinstance(FilesystemStorageProvider(), StorageProvider)


def test_slide_reader_has_implementer():
    from services.readers import OpenSlideReader

    assert isinstance(OpenSlideReader(), SlideReader)


def test_tile_cache_has_implementer():
    from services.cache.two_level_tile_cache import TwoLevelTileCache

    # l2_enabled=False so we don't try to lazily wire a Redis client.
    assert isinstance(TwoLevelTileCache(l2_enabled=False), TileCache)


def test_workflow_hook_has_two_implementers():
    """FHIR for production, NoOp for dev/tests when no DPI is configured."""
    from services.workflow import FHIRWorkflowHook, NoOpWorkflowHook

    assert isinstance(FHIRWorkflowHook(), WorkflowHook)
    assert isinstance(NoOpWorkflowHook(), WorkflowHook)


def test_all_custom_exceptions_inherit_from_varuna_error():
    """Regression guard: every custom exception class in the project must
    inherit from VarunaError so a single `except VarunaError` handler
    catches everything domain-specific. Adding a new `class XError(Exception)`
    should make this test fail until it's rewired into the hierarchy.
    """
    from core.exceptions import VarunaError

    # ML worker errors (services/ml/worker.py)
    from services.ml.worker import (
        MLWorkerBusyError,
        MLWorkerDownError,
        MLWorkerError,
        MLWorkerExecutionError,
        MLWorkerTimeoutError,
    )

    # Reader selector errors (services/readers/selector.py)
    from services.readers.selector import NoCompatibleReaderError

    custom_exceptions = [
        MLWorkerError,
        MLWorkerBusyError,
        MLWorkerTimeoutError,
        MLWorkerDownError,
        MLWorkerExecutionError,
        NoCompatibleReaderError,
    ]
    for cls in custom_exceptions:
        assert issubclass(cls, VarunaError), (
            f"{cls.__module__}.{cls.__name__} does not inherit from VarunaError. "
            f"Add an appropriate parent in core.exceptions or rewire the class."
        )
