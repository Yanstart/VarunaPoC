"""
Pytest Configuration and Fixtures

Fixtures partagés pour tous les tests du backend.

Documentation:
    - Fixtures: https://docs.pytest.org/en/stable/fixture.html
    - FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
"""

# Ensure the backend root (parent of this tests/ directory) is on sys.path
# so that `from core.xxx import yyy` resolves correctly in all environments.
import os
import sys
from pathlib import Path

_BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

# IMPORTANT: Configure OpenSlide DLL path BEFORE any openslide import
import asyncio

# Configure OpenSlide for Windows (MSYS2 UCRT64 installation)
OPENSLIDE_PATH = r"C:\msys64\ucrt64\bin"
if os.path.exists(OPENSLIDE_PATH) and sys.version_info >= (3, 8):
    os.add_dll_directory(OPENSLIDE_PATH)

import pytest
from fastapi.testclient import TestClient


def _run_async(coro):
    """Run an async coroutine safely, even if an event loop is already running (Windows fix)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture(autouse=True, scope="session")
def db_cleanup_annotations():
    """Clean stale test data once at the start of the test session."""

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


@pytest.fixture
def client():
    """
    FastAPI test client.

    Disposes the async engine after each test to prevent connection
    pool state from leaking between tests.

    Usage:
        def test_endpoint(client):
            response = client.get("/api/health")
            assert response.status_code == 200
    """
    from main import app

    with TestClient(app) as c:
        yield c

    # Dispose the engine to reset connection pool state
    from core.database import engine

    _run_async(engine.dispose())


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
