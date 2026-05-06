"""Unit tests for FilesystemStorageProvider.

Most tests patch slide_scanner internals (the cache + scan function) so we
can drive the provider deterministically without depending on actual slide
files on disk. The integration test that hits real /Slides files lives
elsewhere (test_pacs_integration.py covers part of that path already).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from core.exceptions.storage import SlideNotFoundError, StorageError
from core.interfaces.storage import SlideMetadata
from services.storage_provider import (
    FilesystemStorageProvider,
    _scanner_dict_to_metadata,
    get_storage_provider,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_scanner_dict(
    *,
    slide_id: str = "abc123",
    name: str = "sample.mrxs",
    fmt: str = "MIRAX",
    fmt_string: str = "mirax",
    path: str = "/slides/sample.mrxs",
) -> dict:
    return {
        "id": slide_id,
        "name": name,
        "path": path,
        "format": fmt,
        "format_string": fmt_string,
        "structure_type": "with-companion-dir",
        "has_joint_files": False,
        "joint_files_count": 0,
        "has_companion_dirs": True,
        "companion_dirs_count": 1,
        "detection_method": "extension+detect_format",
        "is_validated": True,
    }


@pytest.fixture
def scanner_cache_with_two_slides():
    """Patch slide_scanner._slide_data_cache and scan_slides_directory."""
    s1 = _make_scanner_dict(slide_id="abc123", name="sample.mrxs", fmt_string="mirax")
    s2 = _make_scanner_dict(
        slide_id="def456",
        name="other.svs",
        fmt="Aperio SVS",
        fmt_string="aperio",
        path="/slides/sub/other.svs",
    )

    cache = {"abc123": s1, "def456": s2}
    with patch.dict("services.storage_provider._slide_data_cache", cache, clear=True), patch(
        "services.storage_provider.scan_slides_directory",
        return_value=[s1, s2],
    ):
        yield cache


# ---------------------------------------------------------------------------
# Mapping helper
# ---------------------------------------------------------------------------


def test_scanner_dict_to_metadata_maps_core_fields():
    d = _make_scanner_dict()
    meta = _scanner_dict_to_metadata(d)
    assert isinstance(meta, SlideMetadata)
    assert meta.slide_id == "abc123"
    assert meta.name == "sample.mrxs"
    assert meta.format == "MIRAX"
    assert meta.storage_path == "/slides/sample.mrxs"
    # dimensions/level_count are zero until get_metadata() opens the slide
    assert meta.dimensions == (0, 0)
    assert meta.level_count == 0
    # extra detection fields land in properties
    assert meta.properties["format_string"] == "mirax"
    assert meta.properties["structure_type"] == "with-companion-dir"


def test_scanner_dict_to_metadata_strips_none_properties():
    d = {"id": "x", "name": "x.svs", "path": "/p", "format": "X"}
    meta = _scanner_dict_to_metadata(d)
    # No None values inside properties
    assert all(v is not None for v in meta.properties.values())


# ---------------------------------------------------------------------------
# list_slides
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_slides_returns_all_when_no_filters(scanner_cache_with_two_slides):
    provider = FilesystemStorageProvider()
    result = await provider.list_slides()
    assert len(result) == 2
    assert {m.slide_id for m in result} == {"abc123", "def456"}


@pytest.mark.asyncio
async def test_list_slides_filters_by_format_string(scanner_cache_with_two_slides):
    provider = FilesystemStorageProvider()
    result = await provider.list_slides(filters={"format_string": "mirax"})
    assert len(result) == 1
    assert result[0].slide_id == "abc123"


@pytest.mark.asyncio
async def test_list_slides_filters_by_format(scanner_cache_with_two_slides):
    provider = FilesystemStorageProvider()
    result = await provider.list_slides(filters={"format": "Aperio SVS"})
    assert len(result) == 1
    assert result[0].slide_id == "def456"


@pytest.mark.asyncio
async def test_list_slides_with_tags_filter_returns_empty(
    scanner_cache_with_two_slides,
):
    """Scanner has no tag concept; tags filter is a forward-compat no-match."""
    provider = FilesystemStorageProvider()
    result = await provider.list_slides(filters={"tags": ["breast_cancer"]})
    assert result == []


@pytest.mark.asyncio
async def test_list_slides_path_prefix_matches_subdirectory(
    scanner_cache_with_two_slides,
):
    provider = FilesystemStorageProvider()
    result = await provider.list_slides(path="/sub")
    assert len(result) == 1
    assert result[0].slide_id == "def456"


# ---------------------------------------------------------------------------
# get_slide_path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_slide_path_returns_absolute_path():
    provider = FilesystemStorageProvider()
    with patch(
        "services.storage_provider.get_slide_path_by_id",
        return_value="/slides/sample.mrxs",
    ):
        path = await provider.get_slide_path("abc123")
    assert isinstance(path, Path)
    assert str(path).endswith("sample.mrxs")


@pytest.mark.asyncio
async def test_get_slide_path_raises_slide_not_found_when_missing():
    provider = FilesystemStorageProvider()
    with patch(
        "services.storage_provider.get_slide_path_by_id", return_value=None
    ), pytest.raises(SlideNotFoundError):
        await provider.get_slide_path("does_not_exist")


# ---------------------------------------------------------------------------
# get_metadata
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_metadata_patches_dimensions_from_slide_loader(
    scanner_cache_with_two_slides,
):
    provider = FilesystemStorageProvider()
    loader_payload = {
        "width": 100000,
        "height": 80000,
        "level_count": 5,
        "mpp_x": 0.25,
        "mpp_y": 0.25,
        "objective_power": 40,
        "vendor": "3DHISTECH",
    }
    with patch(
        "services.storage_provider._sync_get_metadata", return_value=loader_payload
    ):
        meta = await provider.get_metadata("abc123")

    assert meta.dimensions == (100000, 80000)
    assert meta.level_count == 5
    assert meta.properties["mpp_x"] == 0.25
    assert meta.properties["objective_power"] == 40
    assert meta.properties["vendor"] == "3DHISTECH"


@pytest.mark.asyncio
async def test_get_metadata_raises_slide_not_found(
    scanner_cache_with_two_slides,
):
    provider = FilesystemStorageProvider()
    with pytest.raises(SlideNotFoundError):
        await provider.get_metadata("not_in_cache")


@pytest.mark.asyncio
async def test_get_metadata_wraps_loader_failure_in_storage_error(
    scanner_cache_with_two_slides,
):
    provider = FilesystemStorageProvider()
    with patch(
        "services.storage_provider._sync_get_metadata",
        side_effect=RuntimeError("OpenSlide blew up"),
    ), pytest.raises(StorageError) as exc_info:
        await provider.get_metadata("abc123")
    assert "OpenSlide blew up" in str(exc_info.value)


# ---------------------------------------------------------------------------
# stubs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_store_slide_not_implemented():
    provider = FilesystemStorageProvider()
    with pytest.raises(NotImplementedError):
        await provider.store_slide(file=None, metadata={}, tags=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_delete_slide_not_implemented():
    provider = FilesystemStorageProvider()
    with pytest.raises(NotImplementedError):
        await provider.delete_slide("abc123")


# ---------------------------------------------------------------------------
# stats / streaming
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_storage_stats_aggregates_formats(
    scanner_cache_with_two_slides,
):
    provider = FilesystemStorageProvider()
    # File-system probes (getsize, getmtime) will fail on the fake paths;
    # the implementation handles that path silently. We only assert the
    # format counts since they don't depend on disk state.
    stats = await provider.get_storage_stats()
    assert stats["total_slides"] == 2
    assert stats["formats"] == {"mirax": 1, "aperio": 1}
    assert stats["total_size_bytes"] == 0  # paths don't exist on disk
    assert stats["oldest_slide"] is None
    assert stats["newest_slide"] is None


@pytest.mark.asyncio
async def test_stream_slide_yields_chunks(tmp_path):
    payload = b"x" * (1 << 21)  # 2 MiB
    slide_file = tmp_path / "fake.mrxs"
    slide_file.write_bytes(payload)
    provider = FilesystemStorageProvider()
    # Bypass scanner; point get_slide_path at our temp file directly.
    provider.get_slide_path = AsyncMock(return_value=slide_file)

    chunks = [chunk async for chunk in provider.stream_slide("abc123", chunk_size=1 << 20)]
    assert b"".join(chunks) == payload
    # Each chunk no larger than chunk_size, last chunk may be smaller.
    assert all(len(c) <= (1 << 20) for c in chunks)
    assert sum(len(c) for c in chunks) == len(payload)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


def test_singleton_returns_same_instance():
    a = get_storage_provider()
    b = get_storage_provider()
    assert a is b
