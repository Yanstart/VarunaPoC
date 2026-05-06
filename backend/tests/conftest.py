"""
Pytest Configuration and Shared Fixtures

This file provides fixtures for all test modules.
Organized by module (auth, storage, slides, ml, workflow).

Documentation:
- Pytest fixtures: https://docs.pytest.org/en/stable/fixture.html
- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
- Async fixtures: https://pytest-asyncio.readthedocs.io/
"""

# stdlib
import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock

# Ensure the backend root (parent of this tests/ directory) is on sys.path
# so that `from core.xxx import yyy` resolves correctly in all environments.
_BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

# IMPORTANT: Configure OpenSlide DLL path BEFORE any openslide import.
# Required on Windows with MSYS2 UCRT64 installation.
OPENSLIDE_PATH = r"C:\msys64\ucrt64\bin"
if os.path.exists(OPENSLIDE_PATH) and sys.version_info >= (3, 8):
    os.add_dll_directory(OPENSLIDE_PATH)

# third-party
import pytest
from fastapi.testclient import TestClient

# ============================================================================
# HELPERS
# ============================================================================


def _run_async(coro):
    """Run an async coroutine safely, even if an event loop is already running (Windows fix).

    Creates a dedicated short-lived loop per call that is independent from
    the session-scoped event_loop fixture used by pytest-asyncio.  Do NOT
    use this inside async test functions — it is only for synchronous
    fixtures that must perform one-shot async I/O (DB cleanup, engine dispose).
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """
    Pytest configuration hook — called once at startup.

    Registers custom markers in code so they appear in --markers output even
    when pyproject.toml is not loaded (e.g. running pytest from an IDE).
    Definitions here are redundant with pyproject.toml but explicit.
    """
    # Module markers
    config.addinivalue_line("markers", "auth: Authentication module tests")
    config.addinivalue_line("markers", "storage: Storage provider tests")
    config.addinivalue_line("markers", "slides: Slide loading and tile serving tests")
    config.addinivalue_line("markers", "ml: Machine learning integration tests")
    config.addinivalue_line("markers", "workflow: Workflow hooks tests (PACS, RIS, LIS)")
    config.addinivalue_line("markers", "cache: Tile caching tests")
    # Test type markers
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (require external services)")
    config.addinivalue_line("markers", "slow: Slow tests (>1s)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full stack)")
    # Domain markers (VarunaPoC feature areas)
    config.addinivalue_line("markers", "annotation: Annotation CRUD and schema tests")
    config.addinivalue_line("markers", "db: Tests requiring PostgreSQL database")
    config.addinivalue_line("markers", "detection: Detection pipeline tests")
    config.addinivalue_line("markers", "focus: Focus assist tests")
    config.addinivalue_line("markers", "similarity: Similarity search tests")
    config.addinivalue_line("markers", "counting: Cell counting tests")
    config.addinivalue_line("markers", "clustering: Clustering tests")
    config.addinivalue_line("markers", "drift: Drift detection tests")
    config.addinivalue_line("markers", "quality: Slide quality control tests")
    config.addinivalue_line("markers", "worklist: Worklist and history tests")
    config.addinivalue_line("markers", "retraining: Retraining pipeline tests")
    config.addinivalue_line("markers", "load: Load/performance tests")


def pytest_collection_modifyitems(config, items):
    """
    Auto-add markers during collection based on file location and name.

    Rules applied (in order, non-exclusive — a test can receive multiple markers):
    - tests/unit/  subdirectory  → unit marker
    - tests/integration/ subdirectory → integration marker
    - "auth"    in nodeid → auth marker
    - "storage" in nodeid → storage marker
    - "slide"   in nodeid → slides marker  (matches slide, slides, slide_scanner, etc.)
    - "ml"      in nodeid → ml marker
    - "workflow" in nodeid → workflow marker
    - "cache"   in nodeid → cache marker

    Note: auto-marking via nodeid substring is intentionally broad.  Files like
    test_auth_jwt.py, test_auth_dependencies.py and test_audit.py all receive
    the 'auth' marker, which is correct.  Use explicit @pytest.mark decorators
    to override or refine when needed.
    """
    for item in items:
        nodeid = str(item.nodeid)
        fspath = str(item.fspath)

        # Directory-based markers
        if "tests/unit" in fspath or "tests\\unit" in fspath:
            item.add_marker(pytest.mark.unit)
        if "tests/integration" in fspath or "tests\\integration" in fspath:
            item.add_marker(pytest.mark.integration)

        # Module-based markers (filename/nodeid substring)
        if "auth" in nodeid:
            item.add_marker(pytest.mark.auth)
        if "storage" in nodeid:
            item.add_marker(pytest.mark.storage)
        if "slide" in nodeid:
            item.add_marker(pytest.mark.slides)
        if "ml" in nodeid:
            item.add_marker(pytest.mark.ml)
        if "workflow" in nodeid:
            item.add_marker(pytest.mark.workflow)
        if "cache" in nodeid:
            item.add_marker(pytest.mark.cache)


# ============================================================================
# EVENT LOOP (Async Support)
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """
    Session-scoped event loop for async test functions managed by pytest-asyncio.

    This loop is distinct from the loops created by _run_async(), which are
    short-lived and function-scoped.  Do not close this loop manually inside
    async tests — pytest-asyncio handles teardown via the yield.

    Note: overriding event_loop at session scope produces a DeprecationWarning
    in pytest-asyncio >= 0.21.  This is suppressed in filterwarnings.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE CLEANUP
# ============================================================================


@pytest.fixture(autouse=True, scope="session")
def db_cleanup_annotations():
    """Clean stale test data once at the start of the test session.

    Deletes rows matching test_ prefixes from annotations and annotation_labels
    tables.  Silently skipped when the database is not available (CI without
    PostgreSQL, local dev without Docker).

    Uses _run_async() (not the event_loop fixture) because this fixture is
    synchronous and must not depend on pytest-asyncio's loop lifecycle.
    """

    async def _cleanup():
        try:
            import asyncpg

            conn = await asyncpg.connect(
                host="localhost",
                port=5433,
                user="varuna",
                password="varuna_dev",  # pragma: allowlist secret
                database="varuna",
                timeout=2,
            )
            try:
                await conn.execute("DELETE FROM annotations WHERE slide_id LIKE 'test_%'")
                await conn.execute(
                    "DELETE FROM annotation_labels WHERE name LIKE 'Test%' OR name LIKE 'test_%'"
                )
            finally:
                await conn.close()
        except Exception:
            pass  # DB not available — nothing to clean

    _run_async(_cleanup())


# ============================================================================
# FASTAPI CLIENT FIXTURE
# ============================================================================


@pytest.fixture
def client():
    """
    FastAPI test client.

    Disposes the async engine after each test to prevent connection
    pool state from leaking between tests.

    Usage:
        def test_endpoint(client):
            response = client.get("/api/v1/health")
            assert response.status_code == 200
    """
    from main import app

    with TestClient(app) as c:
        yield c

    # Dispose the engine to reset connection pool state.
    # The lifespan shutdown already calls close_db(), but we dispose
    # again to ensure no pool state leaks between tests.
    try:
        from core.database import engine

        _run_async(engine.dispose())
    except Exception:
        pass  # DB module not available in CI — nothing to clean


@pytest.fixture
def mock_slides_dir(tmp_path):
    """
    Temporary directory for test slides.

    Creates a mock /Slides directory structure for testing.

    Returns:
        Path: Path to temporary slides directory
    """
    slides_dir = tmp_path / "Slides"
    slides_dir.mkdir()

    # Create test folders
    (slides_dir / "3Dhistec").mkdir()
    (slides_dir / "ROCHE").mkdir()

    return slides_dir


@pytest.fixture
def sample_slide_metadata():
    """
    Sample slide metadata for testing.

    Returns metadata that matches OpenSlide format.
    """
    return {
        "slide_id": "test_slide_001",
        "format": "mrxs",
        "vendor": "3DHistech",
        "dimensions": {"width": 100000, "height": 80000},
        "level_count": 9,
        "mpp_x": 0.25,
        "mpp_y": 0.25,
        "objective_power": 40,
    }


# ============================================================================
# AUTH MODULE FIXTURES
# ============================================================================


@pytest.fixture
def mock_user():
    """
    Mock authenticated user.

    Returns:
        User object with typical fields
    """
    try:
        from core.interfaces.auth import User

        return User(
            user_id="user123",
            username="test_pathologist",
            email="pathologist@chu-ucl.be",
            roles=["pathologist", "user"],
            metadata={"department": "pathology", "hospital": "CHU UCL"},
        )
    except ImportError:
        # Fallback if interfaces not available
        return {
            "user_id": "user123",
            "username": "test_pathologist",
            "roles": ["pathologist"],
        }


@pytest.fixture
def mock_auth_provider():
    """
    Mock AuthProvider for testing.

    Returns User instances (matching the AuthProvider Protocol contract)
    rather than raw dicts so attribute access works in tests.
    """
    from core.interfaces.auth import User

    provider = AsyncMock()

    async def mock_authenticate(credentials: Dict[str, Any]):
        if credentials.get("username") == "test_pathologist":
            return User(
                user_id="user123",
                username="test_pathologist",
                email="pathologist@chu-ucl.be",
                roles=["pathologist"],
            )
        return None

    provider.authenticate = AsyncMock(side_effect=mock_authenticate)
    provider.authorize = AsyncMock(return_value=True)

    async def mock_validate_token(token: str):
        if token == "valid_token":
            return User(
                user_id="user123",
                username="test_pathologist",
            )
        return None

    provider.validate_token = AsyncMock(side_effect=mock_validate_token)

    return provider


# ============================================================================
# STORAGE MODULE FIXTURES
# ============================================================================


@pytest.fixture
def mock_slide_metadata_storage():
    """
    Mock slide metadata for storage tests.

    Returns a SlideMetadata instance (matching the StorageProvider Protocol
    contract) so attribute access works in tests.
    """
    from core.interfaces.storage import SlideMetadata

    return SlideMetadata(
        slide_id="abc123",
        name="sample.mrxs",
        format="mirax",
        dimensions=(100000, 80000),
        level_count=5,
        storage_path="/slides/sample.mrxs",
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        tags=["breast_cancer", "high_priority"],
        properties={"vendor": "3DHISTECH", "magnification": "40x"},
    )


@pytest.fixture
def mock_slide_metadata(mock_slide_metadata_storage):
    """Alias for mock_slide_metadata_storage. The _storage suffix exists to
    avoid clashes with slide-loader-style metadata fixtures; tests in
    tests/unit/test_storage_interface.py use the unsuffixed name."""
    return mock_slide_metadata_storage


@pytest.fixture
def mock_storage_provider(mock_slide_metadata_storage):
    """
    Mock StorageProvider for testing.
    """
    provider = AsyncMock()

    provider.list_slides = AsyncMock(return_value=[mock_slide_metadata_storage])
    provider.get_slide_path = AsyncMock(return_value=Path("/slides/sample.mrxs"))
    provider.get_metadata = AsyncMock(return_value=mock_slide_metadata_storage)
    provider.store_slide = AsyncMock(return_value="abc123")
    provider.delete_slide = AsyncMock(return_value=True)
    provider.get_storage_stats = AsyncMock(
        return_value={
            "total_slides": 100,
            "total_size_bytes": 5_000_000_000,
            "formats": {"mrxs": 60, "bif": 30, "svs": 10},
        }
    )

    return provider


# ============================================================================
# CACHE MODULE FIXTURES
# ============================================================================


@pytest.fixture
def mock_tile_cache():
    """
    Mock TileCache for testing.
    """
    cache = AsyncMock()
    cache._storage = {}

    async def mock_get_tile(slide_id, level, col, row, tile_size=256):
        key = f"{slide_id}:{level}:{col}_{row}:{tile_size}"
        return cache._storage.get(key)

    cache.get_tile = AsyncMock(side_effect=mock_get_tile)

    async def mock_set_tile(slide_id, level, col, row, tile_size, data, ttl=None):
        key = f"{slide_id}:{level}:{col}_{row}:{tile_size}"
        cache._storage[key] = data
        return True

    cache.set_tile = AsyncMock(side_effect=mock_set_tile)

    cache.get_stats = AsyncMock(
        return_value={
            "hit_rate": 0.75,
            "miss_rate": 0.25,
            "total_requests": 1000,
        }
    )

    return cache


# ============================================================================
# WORKFLOW MODULE FIXTURES
# ============================================================================


@pytest.fixture
def mock_workflow_hook():
    """
    Mock WorkflowHook for testing.
    """
    hook = AsyncMock()

    hook.on_event = AsyncMock(return_value=True)
    hook.query_worklist = AsyncMock(
        return_value=[
            {
                "accession_number": "A2025-001",
                "patient_id": "12345",
                "patient_name": "DOE^JOHN",
                "study_date": "2025-01-01",
            }
        ]
    )
    hook.send_result = AsyncMock(return_value=True)

    return hook


# ============================================================================
# TEMP DIRECTORIES
# ============================================================================


@pytest.fixture
def temp_slides_dir(tmp_path):
    """
    Create temporary slides directory for testing.
    """
    slides_dir = tmp_path / "slides"
    slides_dir.mkdir()
    return slides_dir


# ============================================================================
# SKIP MARKERS (Conditional Test Execution)
# ============================================================================


def pytest_runtest_setup(item):
    """
    Skip tests based on markers if dependencies not available.
    """
    # Skip tests marked with 'requires_openslide'
    if "requires_openslide" in [mark.name for mark in item.iter_markers()]:
        try:
            import openslide  # noqa: F401
        except ImportError:
            pytest.skip("OpenSlide not installed")

    # Skip tests marked with 'requires_redis'
    if "requires_redis" in [mark.name for mark in item.iter_markers()]:
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379)
            r.ping()
        except Exception:
            pytest.skip("Redis not available")

    # Skip tests marked with 'requires_pacs'
    if "requires_pacs" in [mark.name for mark in item.iter_markers()] and not os.getenv("PACS_SERVER"):
        pytest.skip("PACS server not configured")

    # Skip tests marked with 'requires_fhir'
    if "requires_fhir" in [mark.name for mark in item.iter_markers()]:
        try:
            import httpx

            base_url = os.getenv("FHIR_BASE_URL", "http://localhost:8090/fhir").rstrip("/")
            with httpx.Client(timeout=2.0) as client:
                client.get(f"{base_url}/metadata")
        except Exception:
            pytest.skip(f"FHIR server not reachable at {base_url!r}")

    # Skip tests marked with 'requires_orthanc' (PACSWorkflowHook integration tests)
    if "requires_orthanc" in [mark.name for mark in item.iter_markers()]:
        try:
            from pynetdicom import AE  # type: ignore[import-untyped]

            host = os.getenv("PACS_HOST", "localhost")
            port = int(os.getenv("PACS_DICOM_PORT", "4242"))
            local_aet = os.getenv("PACS_AET_LOCAL", "VARUNA_TEST")
            remote_aet = os.getenv("PACS_AET_REMOTE", "ORTHANC")
            ae = AE(ae_title=local_aet)
            ae.add_requested_context("1.2.840.10008.1.1")  # Verification SOP
            assoc = ae.associate(host, port, ae_title=remote_aet)
            try:
                if not assoc.is_established:
                    pytest.skip(f"Orthanc PACS association rejected at {host}:{port}")
            finally:
                if assoc.is_established:
                    assoc.release()
        except Exception as e:
            pytest.skip(f"Orthanc PACS not reachable: {e}")
