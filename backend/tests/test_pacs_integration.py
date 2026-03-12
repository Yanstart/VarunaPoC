"""
Tests for PACS Telemis integration (Phase 3.3).

Tests the /api/slides/by-name/{slide_name} endpoint used by Telemis PACS
to resolve slides by filename stem (examindex).
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# Mock slide data matching scan_slides_directory() output shape
MOCK_SLIDES = [
    {
        "id": "abc123",
        "name": "AO.25B27859.2.1.3.mrxs",
        "path": "/slides/AO.25B27859.2.1.3.mrxs",
        "format": "MIRAX",
        "format_string": "mirax",
        "structure_type": "with-companion-dir",
        "has_joint_files": False,
        "joint_files_count": 0,
        "has_companion_dirs": True,
        "companion_dirs_count": 1,
        "detection_method": "extension+openslide",
        "is_supported": True,
        "notes": "",
    },
    {
        "id": "def456",
        "name": "slide_normal.svs",
        "path": "/slides/slide_normal.svs",
        "format": "Aperio SVS",
        "format_string": "aperio",
        "structure_type": "single-file",
        "has_joint_files": False,
        "joint_files_count": 0,
        "has_companion_dirs": False,
        "companion_dirs_count": 0,
        "detection_method": "extension+openslide",
        "is_supported": True,
        "notes": "",
    },
]


def _patch_scanner(mock_slides=None):
    """Return patch context for slide_scanner caches."""
    slides = mock_slides if mock_slides is not None else MOCK_SLIDES
    cache = {s["id"]: s["path"] for s in slides}
    data_cache = {s["id"]: s for s in slides}
    return patch.multiple(
        "services.slide_scanner",
        _slide_cache=cache,
        _slide_data_cache=data_cache,
    )


class TestByNameEndpoint:
    """Tests for GET /api/slides/by-name/{slide_name}."""

    def test_by_name_not_found(self):
        """404 when no slide matches the given name."""
        with _patch_scanner():
            resp = client.get("/api/v1/slides/by-name/nonexistent")
        assert resp.status_code == 404
        assert "nonexistent" in resp.json()["detail"]

    def test_by_name_found(self):
        """200 with full slide data when stem matches."""
        with _patch_scanner():
            resp = client.get("/api/v1/slides/by-name/AO.25B27859.2.1.3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "abc123"
        assert data["name"] == "AO.25B27859.2.1.3.mrxs"
        assert data["format"] == "MIRAX"

    def test_by_name_ambiguous(self):
        """409 when multiple slides match (ambiguous)."""
        # Two slides with same stem but different extensions
        ambiguous = [
            {**MOCK_SLIDES[0], "id": "aaa", "name": "dup.mrxs"},
            {**MOCK_SLIDES[1], "id": "bbb", "name": "dup.svs"},
        ]
        with _patch_scanner(ambiguous):
            resp = client.get("/api/v1/slides/by-name/dup")
        assert resp.status_code == 409
        assert "Ambiguous" in resp.json()["detail"]

    def test_by_name_case_insensitive(self):
        """Match is case-insensitive."""
        with _patch_scanner():
            resp = client.get("/api/v1/slides/by-name/ao.25b27859.2.1.3")
        assert resp.status_code == 200
        assert resp.json()["id"] == "abc123"

    def test_by_name_dots_in_name(self):
        """Multi-dot names work via :path converter."""
        with _patch_scanner():
            # The name has 4 dots: AO.25B27859.2.1.3
            resp = client.get("/api/v1/slides/by-name/AO.25B27859.2.1.3")
        assert resp.status_code == 200
        assert resp.json()["id"] == "abc123"
