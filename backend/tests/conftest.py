"""
Pytest Configuration and Fixtures

Fixtures partagés pour tous les tests du backend.

Documentation:
    - Fixtures: https://docs.pytest.org/en/stable/fixture.html
    - FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
"""

# IMPORTANT: Configure OpenSlide DLL path BEFORE any openslide import
import os
import sys

# Configure OpenSlide for Windows (MSYS2 UCRT64 installation)
OPENSLIDE_PATH = r"C:\msys64\ucrt64\bin"
if os.path.exists(OPENSLIDE_PATH) and sys.version_info >= (3, 8):
    os.add_dll_directory(OPENSLIDE_PATH)

import pytest
from fastapi.testclient import TestClient


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
