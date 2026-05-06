"""
Filesystem StorageProvider — Strangler Fig adapter over the existing
slide_scanner + format_detector + slide_loader stack, exposed under the
StorageProvider Protocol from core.interfaces.storage.

Why this exists
---------------
The Protocol architecture (docs/architecture/MODULAR_ARCHITECTURE.md)
defines StorageProvider as the canonical boundary between VarunaPoC and
the slide storage substrate (filesystem today, S3 / PACS / hybrid later).
This adapter is the first concrete implementer. It composes three
existing modules without changing their behaviour:

- services.slide_scanner       — scan + cache the /Slides directory
- services.format_detector     — validate file format via OpenSlide
- services.slide_loader        — extract per-slide metadata via OpenSlide

The underlying calls are synchronous (OpenSlide is a C library binding
without an async API). The Protocol is async, so we wrap each call in
asyncio.to_thread to keep the FastAPI event loop free.

Methods implemented
-------------------
- list_slides       : full implementation, supports `path` prefix +
                      `recursive` + `format`/`tags` filters.
- get_slide_path    : returns the absolute filesystem path from cache.
- get_metadata      : opens the slide once via slide_loader, maps to
                      Protocol SlideMetadata.
- get_storage_stats : aggregates slide_scanner cache.
- stream_slide      : async generator over file chunks.

Methods stubbed (raise NotImplementedError)
-------------------------------------------
- store_slide  : multi-file slide ingestion (.mrxs + companion folder)
                 needs design that is out of scope for the Strangler Fig.
                 Today, slides are added by dropping files in /Slides
                 manually, then triggering rescan().
- delete_slide : RGPD/HIPAA delete needs the audit pipeline + soft/hard
                 distinction implemented at the route layer. Stub flags
                 the gap for the follow-up commit.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, BinaryIO, Dict, List, Optional

from core.exceptions.storage import SlideNotFoundError, StorageError
from core.interfaces.storage import SlideMetadata
from services.format_detector import FormatDetector
from services.slide_loader import get_slide_metadata as _sync_get_metadata
from services.slide_scanner import (
    _slide_data_cache,
    get_slide_path_by_id,
    invalidate_cache,
    rescan,
    scan_slides_directory,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _scanner_dict_to_metadata(d: Dict[str, Any]) -> SlideMetadata:
    """Translate a slide_scanner dict (legacy shape) into a Protocol SlideMetadata.

    The scanner dict is broader than the Protocol model — extra keys flow
    into `properties` so callers that need format-detection details
    (structure_type, joint files, detection_method) can still get them.
    """
    file_path = d.get("path", "")
    dimensions = (0, 0)
    level_count = 0

    # We don't open the slide here (cheap path). dimensions / level_count
    # stay zero until get_metadata() is called and the slide is actually
    # opened. Callers that only need to enumerate slides skip the cost.
    properties = {
        "structure_type": d.get("structure_type"),
        "has_joint_files": d.get("has_joint_files"),
        "joint_files_count": d.get("joint_files_count"),
        "has_companion_dirs": d.get("has_companion_dirs"),
        "companion_dirs_count": d.get("companion_dirs_count"),
        "detection_method": d.get("detection_method"),
        "format_string": d.get("format_string"),
        "is_validated": d.get("is_validated", False),
    }
    # Strip None values to keep the payload clean.
    properties = {k: v for k, v in properties.items() if v is not None}

    created_at: Optional[datetime] = None
    if file_path:
        try:
            mtime = Path(file_path).stat().st_mtime
            created_at = datetime.fromtimestamp(mtime, tz=UTC)
        except OSError:
            created_at = None

    return SlideMetadata(
        slide_id=d.get("id", ""),
        name=d.get("name", ""),
        format=d.get("format", "unknown"),
        dimensions=dimensions,
        level_count=level_count,
        storage_path=file_path,
        created_at=created_at,
        tags=[],
        properties=properties,
    )


def _matches_filters(d: Dict[str, Any], filters: Optional[Dict]) -> bool:
    """Apply optional list_slides filters against a scanner dict.

    Supported filter keys (others ignored):
      - "format"        : exact match against the human-readable format
      - "format_string" : exact match against the OpenSlide format string
      - "tags"          : ALL tags must be present (today scanner has no
                          tag concept, so this filter never matches —
                          documented for forward compat)
    """
    if not filters:
        return True
    if "format" in filters and d.get("format") != filters["format"]:
        return False
    if "format_string" in filters and d.get("format_string") != filters["format_string"]:
        return False
    # Scanner dicts have no tags today; treat presence of a tags filter as
    # "no slide matches" rather than crashing — forward-compat for when
    # tagging is added.
    return "tags" not in filters


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class FilesystemStorageProvider:
    """StorageProvider Protocol implementer over the local /Slides directory.

    Stateless: a single instance can serve every request. Wired as a
    singleton via `get_storage_provider()`.
    """

    def __init__(self, slides_dir: Optional[str] = None) -> None:
        # None defers to slide_scanner.SLIDES_ROOT (env-driven default).
        self._slides_dir = slides_dir
        self._format_detector = FormatDetector()

    # -- listing --------------------------------------------------------------

    async def list_slides(
        self,
        path: str = "/",
        recursive: bool = False,
        filters: Optional[Dict] = None,
    ) -> List[SlideMetadata]:
        """Return slides under the cache, optionally filtered.

        Notes on `path` and `recursive`:
        - The legacy scanner is *always* recursive; passing `recursive=False`
          is honoured by post-filtering on parent directory equality.
        - `path="/"` returns everything.
        - The leading "/" in `path` is stripped to relative form before
          matching against scanner-relative paths.
        """
        slides: List[Dict[str, Any]] = await asyncio.to_thread(
            scan_slides_directory, self._slides_dir
        )

        # Path filter
        prefix = path.lstrip("/").replace("\\", "/")
        if prefix:
            slides = [
                s
                for s in slides
                if Path(s["path"]).as_posix().lower().find(f"/{prefix.lower()}") != -1
            ]

        # Optional per-field filters
        if filters:
            slides = [s for s in slides if _matches_filters(s, filters)]

        return [_scanner_dict_to_metadata(s) for s in slides]

    # -- single-slide lookup -------------------------------------------------

    async def get_slide_path(self, slide_id: str) -> Path:
        """Return the absolute filesystem path of the slide entry point."""
        path = await asyncio.to_thread(get_slide_path_by_id, slide_id)
        if not path:
            raise SlideNotFoundError(slide_id)
        return Path(path)

    async def get_metadata(self, slide_id: str) -> SlideMetadata:
        """Open the slide once to extract real dimensions, level_count, etc."""
        scanner_dict = _slide_data_cache.get(slide_id)
        if scanner_dict is None:
            # Trigger a lazy populate, then re-check.
            await asyncio.to_thread(scan_slides_directory, self._slides_dir)
            scanner_dict = _slide_data_cache.get(slide_id)
        if scanner_dict is None:
            raise SlideNotFoundError(slide_id)

        slide_path = scanner_dict["path"]
        try:
            loader_dict = await asyncio.to_thread(_sync_get_metadata, slide_path)
        except Exception as e:
            raise StorageError(
                f"Failed to extract metadata for slide_id={slide_id!r}: {e}",
                details={"slide_id": slide_id, "error": str(e)},
            ) from e

        meta = _scanner_dict_to_metadata(scanner_dict)
        # Patch in real dimensions from slide_loader.
        meta.dimensions = (
            int(loader_dict.get("width", 0)),
            int(loader_dict.get("height", 0)),
        )
        meta.level_count = int(loader_dict.get("level_count", 0))
        # Promote selected loader fields into properties for callers.
        for key in ("mpp_x", "mpp_y", "objective_power", "vendor", "level_dimensions"):
            value = loader_dict.get(key)
            if value is not None:
                meta.properties[key] = value
        return meta

    # -- mutation (stubs) ----------------------------------------------------

    async def store_slide(
        self,
        file: BinaryIO,
        metadata: Dict,
        tags: Optional[List[str]] = None,
    ) -> str:
        msg = (
            "FilesystemStorageProvider.store_slide is not implemented. "
            "Multi-file slide ingestion (e.g. .mrxs + companion folder) "
            "needs a dedicated upload pipeline. Today, drop files in /Slides "
            "and call rescan(). Track in a follow-up commit."
        )
        raise NotImplementedError(msg)

    async def delete_slide(
        self, slide_id: str, permanent: bool = False
    ) -> bool:
        msg = (
            "FilesystemStorageProvider.delete_slide is not implemented. "
            "Soft/hard delete needs to be wired through the audit trail and "
            "RGPD pipeline (right-to-be-forgotten flow). Track in a follow-up."
        )
        raise NotImplementedError(msg)

    # -- stats / streaming ---------------------------------------------------

    async def get_storage_stats(self) -> Dict:
        """Aggregate scanner cache + filesystem sizes."""
        # Make sure the cache is populated (cheap if already warm).
        await asyncio.to_thread(scan_slides_directory, self._slides_dir)

        slides = list(_slide_data_cache.values())
        total_slides = len(slides)
        total_size_bytes = 0
        formats: Dict[str, int] = {}
        oldest: Optional[datetime] = None
        newest: Optional[datetime] = None

        for s in slides:
            fmt = s.get("format_string", s.get("format", "unknown"))
            formats[fmt] = formats.get(fmt, 0) + 1
            try:
                stat = Path(s["path"]).stat()
                total_size_bytes += stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
                if oldest is None or mtime < oldest:
                    oldest = mtime
                if newest is None or mtime > newest:
                    newest = mtime
            except OSError:
                # Slide path moved/removed since cache was built; skip.
                continue

        return {
            "total_slides": total_slides,
            "total_size_bytes": total_size_bytes,
            "formats": formats,
            "oldest_slide": oldest,
            "newest_slide": newest,
        }

    async def stream_slide(
        self, slide_id: str, chunk_size: int = 1 << 20
    ) -> AsyncIterator[bytes]:
        """Yield the slide file in fixed-size chunks (default 1 MiB).

        For a multi-file format like MIRAX, this streams the **entry point**
        only; consumers that need the full bundle must enumerate companion
        files separately. Documented but acknowledged as a known gap.
        """
        path = await self.get_slide_path(slide_id)
        # Sync read in a thread so the loop is not blocked on disk.

        def _open_and_read():
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        return
                    yield chunk

        gen = _open_and_read()
        loop = asyncio.get_running_loop()
        while True:
            chunk = await loop.run_in_executor(None, next, gen, b"")
            if not chunk:
                return
            yield chunk

    # -- maintenance helper (not on the Protocol) ----------------------------

    async def refresh(self) -> int:
        """Force a rescan and return the number of slides discovered.

        Not part of the Protocol contract — an admin convenience exposed for
        future routes. Equivalent to slide_scanner.rescan() but async and
        thread-safe.
        """
        slides = await asyncio.to_thread(rescan)
        return len(slides)

    async def invalidate(self) -> None:
        """Drop the scanner cache. Next list/get triggers a fresh scan."""
        await asyncio.to_thread(invalidate_cache)


# ---------------------------------------------------------------------------
# Singleton wiring
# ---------------------------------------------------------------------------

_singleton: Optional[FilesystemStorageProvider] = None


def get_storage_provider() -> FilesystemStorageProvider:
    """Return the process-wide FilesystemStorageProvider instance.

    Stateless and cheap; lazily created so import order and test isolation
    are not constrained.
    """
    global _singleton
    if _singleton is None:
        _singleton = FilesystemStorageProvider()
    return _singleton


__all__ = ["FilesystemStorageProvider", "get_storage_provider"]
