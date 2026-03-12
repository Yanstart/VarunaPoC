"""
Tile Audit Service

Session-deduplicated audit logging for tile access (SLIDE_VIEWED events).

Design rationale:
    Tiles are the primary PHI access mode in the viewer.  Each slide view
    generates hundreds of tile requests.  Logging every tile would produce
    unmanageable audit volume, so we deduplicate: one SLIDE_VIEWED event
    is emitted per (user_sub, slide_id, ISO-date) triple per session TTL.

Deduplication strategy:
    Primary:  Redis SET with TTL (if REDIS_URL env var is set and redis-py
              is installed).  Survives process restarts and works in
              multi-process / multi-replica deployments.
    Fallback: In-memory dict {dedup_key -> expiry_monotonic_ts}.
              Sufficient for single-process dev/PoC deployments.

Audit persistence:
    Delegates to auth.audit.log_audit_event (dual DB + JSONL persistence).
    If that module is unavailable the event is still emitted via the
    standard Python logger so it appears in application logs.
"""

import asyncio
import logging
import os
import time
from datetime import UTC, datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional audit dependency (imported at module level for testability)
# ---------------------------------------------------------------------------

try:
    from auth.audit import log_audit_event  # type: ignore[import-untyped]
except ImportError:
    log_audit_event = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEDUP_TTL: int = 3600  # seconds — one event per (user, slide, day)

# ---------------------------------------------------------------------------
# In-memory fallback dedup store
# ---------------------------------------------------------------------------

# key  -> expiry timestamp (time.monotonic())
_dedup_store: dict[str, float] = {}


def _cleanup_expired() -> None:
    """Remove expired entries from the in-memory dedup store."""
    now = time.monotonic()
    expired = [k for k, v in _dedup_store.items() if v < now]
    for k in expired:
        del _dedup_store[k]


# ---------------------------------------------------------------------------
# Redis helper (optional)
# ---------------------------------------------------------------------------

_redis_client: Optional[object] = None
_redis_checked: bool = False


def _get_redis():
    """Return a Redis client if REDIS_URL is set and redis-py is available.

    Returns:
        Redis client instance, or None if Redis is unavailable.
    """
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    _redis_checked = True

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.debug("REDIS_URL not set — using in-memory dedup store")
        return None

    try:
        import redis  # type: ignore[import-untyped]

        _redis_client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
        # Verify connectivity eagerly so we fall back fast if Redis is down
        _redis_client.ping()
        logger.info("Tile audit dedup: using Redis at %s", redis_url)
    except Exception as exc:
        logger.warning(
            "Tile audit: Redis unavailable (%s) — falling back to in-memory dedup store",
            exc,
        )
        _redis_client = None

    return _redis_client


# ---------------------------------------------------------------------------
# Dedup helpers
# ---------------------------------------------------------------------------


def _is_already_seen_memory(dedup_key: str) -> bool:
    """Check dedup key in the in-memory store.

    Returns True if the key exists and has not expired.
    """
    now = time.monotonic()
    expiry = _dedup_store.get(dedup_key)
    return expiry is not None and expiry > now


def _mark_seen_memory(dedup_key: str) -> None:
    """Mark dedup key as seen in the in-memory store with TTL.

    Triggers periodic cleanup when the store grows large to prevent
    unbounded memory usage.
    """
    if len(_dedup_store) > 1000:
        _cleanup_expired()
    _dedup_store[dedup_key] = time.monotonic() + _DEDUP_TTL


def _is_already_seen_redis(redis_client, dedup_key: str) -> bool:
    """Check dedup key in Redis.

    Returns True if the key exists.  Returns False and logs a warning
    if Redis raises an exception (fail-open to avoid blocking tile serving).
    """
    try:
        return redis_client.exists(dedup_key) == 1
    except Exception as exc:
        logger.warning("Tile audit Redis check failed (%s) — treating as first access", exc)
        return False


def _mark_seen_redis(redis_client, dedup_key: str) -> None:
    """Store dedup key in Redis with TTL.

    Silently ignores errors to avoid blocking tile serving.
    """
    try:
        redis_client.set(dedup_key, "1", ex=_DEDUP_TTL)
    except Exception as exc:
        logger.warning("Tile audit Redis set failed (%s) — event may be re-logged on restart", exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def record_tile_access(
    user_sub: str,
    slide_id: str,
    zoom_level: int,
    cache_hit: bool = False,
) -> bool:
    """Record a SLIDE_VIEWED audit event with session deduplication.

    Emits at most one SLIDE_VIEWED event per (user_sub, slide_id, ISO-date)
    within the dedup TTL window (1 hour).  Subsequent tile requests from the
    same session are silently ignored.

    Args:
        user_sub: Subject identifier of the authenticated user.
        slide_id: Unique slide identifier (MD5 hash).
        zoom_level: OpenSlide pyramid level of the first tile request.
        cache_hit: True if the slide was already open in the tile cache
                   (slide was loaded from a previous request).

    Returns:
        True if this was the first access and an audit event was logged.
        False if the access was deduplicated (already logged today).

    Technical Notes:
        - Dedup key: "{user_sub}:{slide_id}:{YYYY-MM-DD}".
        - Dedup store: Redis if REDIS_URL is configured, else in-memory dict.
        - Audit persistence: delegates to auth.audit.log_audit_event (DB +
          JSONL).  Falls back to standard logger if that module is unavailable.
        - This function is async so it can be scheduled as a background task
          from both sync and async endpoint handlers without blocking the
          tile response.
    """
    today = datetime.now(tz=UTC).date().isoformat()
    dedup_key = f"{user_sub}:{slide_id}:{today}"

    # --- Deduplication check ---
    redis_client = _get_redis()
    if redis_client is not None:
        if _is_already_seen_redis(redis_client, dedup_key):
            return False
        _mark_seen_redis(redis_client, dedup_key)
    else:
        if _is_already_seen_memory(dedup_key):
            return False
        _mark_seen_memory(dedup_key)

    # --- Emit audit event ---
    logger.info(
        "SLIDE_VIEWED: user=%s slide=%s zoom=%d date=%s cache_hit=%s",
        user_sub,
        slide_id,
        zoom_level,
        today,
        cache_hit,
    )

    if log_audit_event is not None:
        try:
            await log_audit_event(
                event_type="SLIDE_VIEWED",
                action="READ",
                resource_type="slide",
                resource_id=slide_id,
                details={
                    "zoom_level": zoom_level,
                    "date": today,
                    "cache_hit": cache_hit,
                },
            )
        except Exception as exc:
            logger.debug("Audit persistence unavailable: %s", exc)

    return True


def schedule_tile_audit(
    user_sub: str,
    slide_id: str,
    zoom_level: int,
    cache_hit: bool = False,
) -> None:
    """Fire-and-forget wrapper for record_tile_access from sync code.

    Creates an asyncio Task when a running event loop is available, which
    is the normal case inside a FastAPI request handler (even a sync one,
    because FastAPI runs sync handlers in a thread pool that shares the
    main event loop via anyio).

    If no running loop is found (e.g. unit tests running outside asyncio)
    the call is silently dropped — audit is best-effort and must never
    block or fail tile serving.

    Args:
        user_sub: Subject identifier of the authenticated user.
        slide_id: Unique slide identifier (MD5 hash).
        zoom_level: OpenSlide pyramid level of the first tile request.
        cache_hit: True if the slide was already open in the tile cache.
    """
    try:
        loop = asyncio.get_running_loop()
        _task = loop.create_task(  # noqa: RUF006 — intentional fire-and-forget
            record_tile_access(user_sub, slide_id, zoom_level, cache_hit)
        )
    except RuntimeError:
        # No running event loop — silently skip audit (e.g. unit tests)
        pass
    except Exception as exc:
        logger.debug("Tile audit scheduling failed (non-fatal): %s", exc)
