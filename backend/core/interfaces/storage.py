"""
Storage Provider Interface

DESIGN PRINCIPLE: Storage Abstraction
Decouple slide storage from viewer logic. Supports:
- Filesystem (current implementation)
- S3/MinIO (cloud storage)
- PACS DICOM (hospital integration)
- Hybrid (local cache + remote storage)

Why this matters:
- CHU may want slides on NAS (filesystem)
- University may want S3 (scalability)
- Hospital may mandate PACS integration (DICOM Q/R)
- VarunaPoC should work with ALL without code changes

Pattern: Strategy Pattern + Adapter Pattern
"""

from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, BinaryIO, Dict, List, Optional, Protocol, runtime_checkable


class SlideMetadata:
    """
    Minimal slide metadata (format-agnostic).
    Extended by format-specific loaders.
    """
    def __init__(
        self,
        slide_id: str,
        name: str,
        format: str,
        dimensions: tuple[int, int],
        level_count: int,
        storage_path: str,
        created_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        properties: Optional[Dict] = None
    ):
        self.slide_id = slide_id
        self.name = name
        self.format = format
        self.dimensions = dimensions
        self.level_count = level_count
        self.storage_path = storage_path
        self.created_at = created_at or datetime.now()
        self.tags = tags or []
        self.properties = properties or {}


@runtime_checkable
class StorageProvider(Protocol):
    """
    Protocol for pluggable storage backends.

    Implementations:
    - FilesystemStorageProvider (Phase 1 - current)
    - S3StorageProvider (Phase 2 - cloud)
    - PacsStorageProvider (Phase 2 - DICOM integration)
    - HybridStorageProvider (Phase 3 - cache + remote)

    Design Notes:
    - All methods MUST be async (non-blocking I/O)
    - Implementations MUST handle errors gracefully
    - Implementations SHOULD cache metadata when possible
    """

    async def list_slides(
        self,
        path: str = "/",
        recursive: bool = False,
        filters: Optional[Dict] = None
    ) -> List[SlideMetadata]:
        """
        List slides in a directory/prefix.

        Args:
            path: Relative path (filesystem) or prefix (S3)
            recursive: If True, scan subdirectories
            filters: Optional filters (e.g., {"format": "mrxs", "tags": ["breast_cancer"]})

        Returns:
            List of SlideMetadata objects

        Examples:
            >>> # Filesystem
            >>> slides = await provider.list_slides(path="/3DHistech", recursive=False)

            >>> # S3
            >>> slides = await provider.list_slides(path="slides/2024/", recursive=True)

            >>> # PACS (query worklist)
            >>> slides = await provider.list_slides(
            ...     path="/",
            ...     filters={"patient_id": "12345", "modality": "SM"}
            ... )

        Notes:
            - Filesystem: Use format_detector.py (existing)
            - S3: Use boto3.list_objects_v2 with prefix
            - PACS: Use DICOM C-FIND query
        """
        ...

    async def get_slide_path(
        self,
        slide_id: str
    ) -> Path:
        """
        Get local path to slide file.

        Args:
            slide_id: Unique slide identifier

        Returns:
            Absolute path to slide file (local filesystem)

        Behavior:
            - Filesystem: Return path directly
            - S3: Download to temp cache, return cached path
            - PACS: Retrieve via C-MOVE, return local path

        Notes:
            - MUST be idempotent (multiple calls return same path)
            - SHOULD cache downloads (avoid re-downloading)
            - MUST handle concurrent requests (file locks)

        Examples:
            >>> path = await provider.get_slide_path("abc123")
            >>> # path: /slides/3DHistech/sample.mrxs (filesystem)
            >>> # path: /tmp/cache/abc123.mrxs (S3)
            >>> # path: /tmp/pacs/abc123.dcm (PACS)
        """
        ...

    async def get_metadata(
        self,
        slide_id: str
    ) -> SlideMetadata:
        """
        Get slide metadata without opening slide.

        Args:
            slide_id: Unique slide identifier

        Returns:
            SlideMetadata object

        Notes:
            - SHOULD cache metadata (avoid repeated OpenSlide calls)
            - MUST include dimensions, level_count, format
            - MAY include vendor-specific properties

        Examples:
            >>> metadata = await provider.get_metadata("abc123")
            >>> print(metadata.dimensions)  # (100000, 80000)
            >>> print(metadata.format)  # "mirax"
        """
        ...

    async def store_slide(
        self,
        file: BinaryIO,
        metadata: Dict,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Store a new slide.

        Args:
            file: Binary file object (or file path)
            metadata: Slide metadata (name, patient_id, etc.)
            tags: Optional tags for ML routing

        Returns:
            slide_id (unique identifier)

        Behavior:
            - Filesystem: Copy to /Slides directory
            - S3: Upload with put_object
            - PACS: Store via C-STORE (DICOM)

        Notes:
            - MUST generate unique slide_id (UUID or hash)
            - SHOULD validate file format (OpenSlide.detect_format)
            - SHOULD extract metadata (OpenSlide properties)
            - MUST handle companion files (.mrxs + folder)

        Examples:
            >>> with open("sample.mrxs", "rb") as f:
            ...     slide_id = await provider.store_slide(
            ...         file=f,
            ...         metadata={"name": "sample", "patient_id": "12345"},
            ...         tags=["breast_cancer", "high_priority"]
            ...     )
        """
        ...

    async def delete_slide(
        self,
        slide_id: str,
        permanent: bool = False
    ) -> bool:
        """
        Delete slide (soft or hard delete).

        Args:
            slide_id: Slide to delete
            permanent: If True, hard delete. If False, soft delete (mark deleted)

        Returns:
            True if successful

        RGPD/HIPAA Notes:
            - Soft delete: Mark as deleted, keep in archive (audit trail)
            - Hard delete: Permanently remove (right to be forgotten)
            - MUST log deletion event (who, when, why)

        Examples:
            >>> # Soft delete (archive)
            >>> await provider.delete_slide("abc123", permanent=False)

            >>> # Hard delete (RGPD "right to be forgotten")
            >>> await provider.delete_slide("abc123", permanent=True)
        """
        ...

    async def get_storage_stats(self) -> Dict:
        """
        Get storage statistics.

        Returns:
            Dict with keys:
            - total_slides: int
            - total_size_bytes: int
            - formats: Dict[str, int] (format → count)
            - oldest_slide: datetime
            - newest_slide: datetime

        Use Cases:
            - Admin dashboard
            - Storage quota monitoring
            - Migration planning (filesystem → S3)

        Examples:
            >>> stats = await provider.get_storage_stats()
            >>> print(stats)
            {
                "total_slides": 1234,
                "total_size_bytes": 5_000_000_000_000,  # 5 TB
                "formats": {"mrxs": 800, "bif": 400, "svs": 34},
                "oldest_slide": datetime(2020, 1, 1),
                "newest_slide": datetime(2025, 12, 31)
            }
        """
        ...

    async def stream_slide(
        self,
        slide_id: str
    ) -> AsyncIterator[bytes]:
        """
        Stream slide bytes (for large files, avoid loading in memory).

        Args:
            slide_id: Slide to stream

        Yields:
            Chunks of bytes

        Use Cases:
            - Download slide to client
            - Transfer slide between storage providers
            - Backup/archive operations

        Examples:
            >>> async for chunk in provider.stream_slide("abc123"):
            ...     # Write chunk to file/network
            ...     await destination.write(chunk)
        """
        ...


class CachedStorageProvider(StorageProvider, Protocol):
    """
    Extension for storage providers with caching support.

    Use Cases:
    - S3StorageProvider: Cache downloaded slides locally
    - PacsStorageProvider: Cache retrieved DICOM files
    - HybridStorageProvider: Multi-tier cache (memory → disk → remote)

    Caching Strategy:
    - LRU (Least Recently Used) eviction
    - TTL (Time To Live) expiration
    - Size-based limits (max cache size)
    """

    async def cache_slide(
        self,
        slide_id: str,
        ttl: Optional[int] = None
    ) -> Path:
        """
        Explicitly cache slide locally.

        Args:
            slide_id: Slide to cache
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            Path to cached file

        Notes:
            - Called automatically by get_slide_path for remote providers
            - Can be called proactively (pre-warming cache)
        """
        ...

    async def invalidate_cache(
        self,
        slide_id: Optional[str] = None
    ) -> bool:
        """
        Invalidate cache entry (or all if slide_id is None).

        Args:
            slide_id: Specific slide to invalidate, or None for all

        Returns:
            True if successful

        Use Cases:
            - Slide updated on remote storage
            - Cache corruption detected
            - Manual cache clearing
        """
        ...

    async def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with keys:
            - cached_slides: int
            - cache_size_bytes: int
            - cache_hit_rate: float (0.0-1.0)
            - evictions: int (LRU evictions count)

        Examples:
            >>> stats = await provider.get_cache_stats()
            >>> print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
        """
        ...
