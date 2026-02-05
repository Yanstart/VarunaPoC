"""
Unit Tests for Storage Interface

Tests verify the StorageProvider interface behavior with mock implementations.
These tests do NOT test actual filesystem/S3/PACS operations (see integration tests).

Markers:
- @pytest.mark.storage: Storage module tests
- @pytest.mark.unit: Unit tests (auto-added)
"""

import pytest
from pathlib import Path
from datetime import datetime


@pytest.mark.storage
@pytest.mark.asyncio
async def test_list_slides(mock_storage_provider):
    """
    Test listing slides from storage.
    """
    slides = await mock_storage_provider.list_slides(path="/")

    assert len(slides) > 0
    assert slides[0].slide_id == "abc123"
    assert slides[0].name == "sample.mrxs"
    assert slides[0].format == "mirax"


@pytest.mark.storage
@pytest.mark.asyncio
async def test_get_slide_path(mock_storage_provider):
    """
    Test getting slide file path.
    """
    path = await mock_storage_provider.get_slide_path("abc123")

    assert path == Path("/slides/sample.mrxs")
    assert isinstance(path, Path)


@pytest.mark.storage
@pytest.mark.asyncio
async def test_get_metadata(mock_storage_provider, mock_slide_metadata):
    """
    Test getting slide metadata.
    """
    metadata = await mock_storage_provider.get_metadata("abc123")

    assert metadata.slide_id == "abc123"
    assert metadata.dimensions == (100000, 80000)
    assert metadata.level_count == 5
    assert "breast_cancer" in metadata.tags


@pytest.mark.storage
@pytest.mark.asyncio
async def test_store_slide(mock_storage_provider):
    """
    Test storing new slide.
    """
    slide_id = await mock_storage_provider.store_slide(
        file=None,  # Mock doesn't need actual file
        metadata={"name": "new_slide.mrxs", "patient_id": "12345"},
        tags=["lung_cancer"]
    )

    assert slide_id == "abc123"


@pytest.mark.storage
@pytest.mark.asyncio
async def test_delete_slide(mock_storage_provider):
    """
    Test deleting slide.
    """
    result = await mock_storage_provider.delete_slide("abc123", permanent=False)

    assert result is True


@pytest.mark.storage
@pytest.mark.asyncio
async def test_get_storage_stats(mock_storage_provider):
    """
    Test getting storage statistics.
    """
    stats = await mock_storage_provider.get_storage_stats()

    assert stats["total_slides"] == 100
    assert stats["total_size_bytes"] > 0
    assert "mrxs" in stats["formats"]


@pytest.mark.storage
def test_slide_metadata_creation(mock_slide_metadata):
    """
    Test SlideMetadata object creation.
    """
    assert mock_slide_metadata.slide_id == "abc123"
    assert mock_slide_metadata.name == "sample.mrxs"
    assert mock_slide_metadata.format == "mirax"
    assert mock_slide_metadata.dimensions == (100000, 80000)
    assert mock_slide_metadata.level_count == 5
    assert "breast_cancer" in mock_slide_metadata.tags
    assert mock_slide_metadata.properties["vendor"] == "3DHISTECH"
