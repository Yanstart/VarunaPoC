"""
Pytest Configuration and Shared Fixtures

This file provides fixtures for all test modules.
Organized by module (auth, storage, slides, ml, workflow).

Documentation:
- Pytest fixtures: https://docs.pytest.org/en/stable/fixture.html
- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
- Async fixtures: https://pytest-asyncio.readthedocs.io/
"""

import asyncio
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """
    Pytest configuration hook.
    Called once at startup.
    """
    # Register custom markers (redundant with pyproject.toml, but explicit)
    config.addinivalue_line("markers", "auth: Authentication module tests")
    config.addinivalue_line("markers", "storage: Storage provider tests")
    config.addinivalue_line("markers", "slides: Slide loading tests")
    config.addinivalue_line("markers", "ml: Machine learning tests")
    config.addinivalue_line("markers", "workflow: Workflow hooks tests")
    config.addinivalue_line("markers", "cache: Caching tests")
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")


def pytest_collection_modifyitems(config, items):
    """
    Modify test items during collection.
    Auto-add markers based on file location.
    """
    for item in items:
        # Auto-add 'unit' marker to tests in tests/unit/
        if "tests/unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Auto-add 'integration' marker to tests in tests/integration/
        if "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Auto-add module markers based on filename
        if "auth" in item.nodeid:
            item.add_marker(pytest.mark.auth)
        if "storage" in item.nodeid:
            item.add_marker(pytest.mark.storage)
        if "slide" in item.nodeid:
            item.add_marker(pytest.mark.slides)
        if "ml" in item.nodeid:
            item.add_marker(pytest.mark.ml)
        if "workflow" in item.nodeid:
            item.add_marker(pytest.mark.workflow)
        if "cache" in item.nodeid:
            item.add_marker(pytest.mark.cache)


# ============================================================================
# EVENT LOOP (Async Support)
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.
    Scope: session (one loop for all tests)
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# FASTAPI CLIENT FIXTURE (Phase 1 Tests)
# ============================================================================


@pytest.fixture
def client():
    """
    FastAPI test client.

    Usage:
        def test_endpoint(client):
            response = client.get("/api/health")
            assert response.status_code == 200
    """
    # Import main app (with OpenSlide config)
    from main import app

    return TestClient(app)


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

    Returns:
        Mock AuthProvider with predefined behavior
    """
    provider = AsyncMock()

    # Mock authenticate() - returns user for valid credentials
    async def mock_authenticate(credentials: Dict[str, Any]):
        if credentials.get("username") == "test_pathologist":
            return {
                "user_id": "user123",
                "username": "test_pathologist",
                "email": "pathologist@chu-ucl.be",
                "roles": ["pathologist"],
            }
        return None

    provider.authenticate = AsyncMock(side_effect=mock_authenticate)
    provider.authorize = AsyncMock(return_value=True)

    async def mock_validate_token(token: str):
        if token == "valid_token":
            return {"user_id": "user123", "username": "test_pathologist"}
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
    """
    from datetime import datetime

    return {
        "slide_id": "abc123",
        "name": "sample.mrxs",
        "format": "mirax",
        "dimensions": (100000, 80000),
        "level_count": 5,
        "storage_path": "/slides/sample.mrxs",
        "created_at": datetime(2025, 1, 1),
        "tags": ["breast_cancer", "high_priority"],
        "properties": {"vendor": "3DHISTECH", "magnification": "40x"},
    }


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
    import os

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
    if "requires_pacs" in [mark.name for mark in item.iter_markers()]:
        if not os.getenv("PACS_SERVER"):
            pytest.skip("PACS server not configured")
