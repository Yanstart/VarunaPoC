"""
Tests for Worklist & History Endpoints

- GET /api/slides/worklist — assigned cases for the current user
- GET /api/slides/history — recently viewed slides

8 tests covering response shape, field validation, and query params.

Markers: @pytest.mark.worklist, @pytest.mark.unit
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.mark.worklist
@pytest.mark.unit
class TestWorklistEndpoint:
    """Test GET /api/slides/worklist with mocked slide scanner."""

    @pytest.fixture(autouse=True)
    def mock_deps(self):
        """Mock auth and slide scanner dependencies."""
        mock_user = MagicMock()
        mock_user.sub = "test-user-123"
        mock_user.username = "dr.test"
        mock_user.roles = ["MEDECIN"]
        mock_user.has_role.return_value = True
        mock_user.break_glass_active = False

        mock_slides = [
            {
                "id": "slide-001",
                "name": "HE_prostate_2024.svs",
                "path": "/Cases/Patient_001/HE_prostate_2024.svs",
                "format": "svs",
                "has_companions": False,
            },
            {
                "id": "slide-002",
                "name": "HE_breast_2024.svs",
                "path": "/Cases/Patient_002/HE_breast_2024.svs",
                "format": "svs",
                "has_companions": False,
            },
            {
                "id": "slide-003",
                "name": "Ki67_lung_2024.svs",
                "path": "/Cases/Patient_003/Ki67_lung_2024.svs",
                "format": "svs",
                "has_companions": False,
            },
            {
                "id": "slide-004",
                "name": "PAS_kidney_2024.svs",
                "path": "/Cases/Patient_004/PAS_kidney_2024.svs",
                "format": "svs",
                "has_companions": False,
            },
            {
                "id": "slide-005",
                "name": "HER2_breast_2024.svs",
                "path": "/Cases/Patient_005/HER2_breast_2024.svs",
                "format": "svs",
                "has_companions": False,
            },
        ]

        with (
            patch(
                "routes.slides.require_role",
                return_value=lambda: mock_user,
            ),
            patch(
                "routes.slides.get_current_user",
                return_value=mock_user,
            ),
            patch(
                "routes.slides.scan_slides_directory",
                return_value=mock_slides,
            ),
        ):
            yield mock_user, mock_slides

    def test_worklist_returns_items_and_counts(self, client):
        """GET /api/slides/worklist returns items list and counts dict."""
        response = client.get("/api/slides/worklist")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "counts" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["counts"], dict)

    def test_worklist_items_have_required_fields(self, client):
        """Each worklist item has all required fields."""
        response = client.get("/api/slides/worklist")
        data = response.json()
        required_fields = {
            "slide_id",
            "slide_name",
            "case_path",
            "status",
            "assigned_date",
            "is_new",
        }
        for item in data["items"]:
            assert required_fields.issubset(item.keys()), f"Missing fields in {item}"

    def test_worklist_status_values_are_valid(self, client):
        """Status values are one of pending, in_progress, completed."""
        valid_statuses = {"pending", "in_progress", "completed"}
        response = client.get("/api/slides/worklist")
        data = response.json()
        for item in data["items"]:
            assert item["status"] in valid_statuses, f"Invalid status: {item['status']}"

    def test_worklist_counts_match_items(self, client):
        """Counts dict values match actual item counts per status."""
        response = client.get("/api/slides/worklist")
        data = response.json()
        items = data["items"]
        counts = data["counts"]

        for status_key in ["pending", "in_progress", "completed"]:
            actual = sum(1 for item in items if item["status"] == status_key)
            assert (
                counts.get(status_key, 0) == actual
            ), f"Count mismatch for {status_key}: expected {actual}, got {counts.get(status_key)}"

    def test_worklist_assigned_date_is_valid_iso(self, client):
        """assigned_date is a valid ISO format datetime string."""
        response = client.get("/api/slides/worklist")
        data = response.json()
        for item in data["items"]:
            # Should not raise ValueError
            parsed = datetime.fromisoformat(item["assigned_date"])
            assert parsed is not None


@pytest.mark.worklist
@pytest.mark.unit
class TestHistoryEndpoint:
    """Test GET /api/slides/history with mocked slide scanner."""

    @pytest.fixture(autouse=True)
    def mock_deps(self):
        """Mock auth and slide scanner dependencies."""
        mock_user = MagicMock()
        mock_user.sub = "test-user-123"
        mock_user.username = "dr.test"
        mock_user.roles = ["MEDECIN"]
        mock_user.has_role.return_value = True
        mock_user.break_glass_active = False

        mock_slides = [
            {
                "id": "slide-001",
                "name": "HE_prostate_2024.svs",
                "path": "/Cases/P1/HE_prostate_2024.svs",
                "format": "svs",
                "has_companions": False,
            },
            {
                "id": "slide-002",
                "name": "HE_breast_2024.svs",
                "path": "/Cases/P2/HE_breast_2024.svs",
                "format": "svs",
                "has_companions": False,
            },
            {
                "id": "slide-003",
                "name": "Ki67_lung_2024.svs",
                "path": "/Cases/P3/Ki67_lung_2024.svs",
                "format": "svs",
                "has_companions": False,
            },
        ]

        with (
            patch(
                "routes.slides.require_role",
                return_value=lambda: mock_user,
            ),
            patch(
                "routes.slides.get_current_user",
                return_value=mock_user,
            ),
            patch(
                "routes.slides.scan_slides_directory",
                return_value=mock_slides,
            ),
        ):
            yield mock_user, mock_slides

    def test_history_returns_items_and_total(self, client):
        """GET /api/slides/history returns items list and total count."""
        response = client.get("/api/slides/history")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_history_respects_limit_param(self, client):
        """GET /api/slides/history?limit=1 returns at most 1 item."""
        response = client.get("/api/slides/history?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1
        # total should still reflect the full count
        assert data["total"] >= len(data["items"])

    def test_history_items_have_required_fields(self, client):
        """Each history item has all required fields."""
        response = client.get("/api/slides/history")
        data = response.json()
        required_fields = {"slide_id", "slide_name", "viewed_at", "view_count"}
        for item in data["items"]:
            assert required_fields.issubset(item.keys()), f"Missing fields in {item}"
