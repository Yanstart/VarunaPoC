"""
Tests for tile audit session deduplication service.

Verifies that SLIDE_VIEWED events are emitted exactly once per
(user_sub, slide_id, ISO-date) session, regardless of the number
of tile requests made during that session.
"""

from unittest.mock import AsyncMock, patch

import pytest

from services.tile_audit import _dedup_store, record_tile_access


@pytest.fixture(autouse=True)
def clear_dedup():
    """Reset in-memory dedup store before and after each test."""
    _dedup_store.clear()
    yield
    _dedup_store.clear()


@pytest.fixture(autouse=True)
def force_memory_backend():
    """Ensure Redis is not used during unit tests (no REDIS_URL)."""
    with (
        patch("services.tile_audit._redis_checked", False),
        patch("services.tile_audit._redis_client", None),
        patch.dict("os.environ", {}, clear=False) as env,
    ):
        # Remove REDIS_URL if present so _get_redis() returns None
        env.pop("REDIS_URL", None)
        # Reset the checked flag so _get_redis() re-evaluates
        import services.tile_audit as ta

        ta._redis_checked = False
        ta._redis_client = None
        yield
        ta._redis_checked = False
        ta._redis_client = None


class TestFirstAccess:
    """Test that the first tile access emits a SLIDE_VIEWED event."""

    @pytest.mark.asyncio
    async def test_first_access_returns_true(self):
        """First access for a (user, slide, date) triple must return True."""
        result = await record_tile_access("user1", "slide1", 5)
        assert result is True

    @pytest.mark.asyncio
    async def test_first_access_populates_dedup_store(self):
        """First access must mark the key in the dedup store."""
        assert len(_dedup_store) == 0
        await record_tile_access("user1", "slide1", 5)
        assert len(_dedup_store) == 1

    @pytest.mark.asyncio
    async def test_first_access_logs_event(self):
        """First access must attempt to call log_audit_event."""
        mock_log = AsyncMock()
        with patch("services.tile_audit.log_audit_event", mock_log):
            await record_tile_access("user1", "slide1", 5)
        mock_log.assert_awaited_once()
        call_kwargs = mock_log.call_args.kwargs
        assert call_kwargs["event_type"] == "SLIDE_VIEWED"
        assert call_kwargs["resource_id"] == "slide1"
        assert call_kwargs["details"]["zoom_level"] == 5

    @pytest.mark.asyncio
    async def test_first_access_includes_cache_hit_false(self):
        """cache_hit=False must be forwarded to audit details."""
        mock_log = AsyncMock()
        with patch("services.tile_audit.log_audit_event", mock_log):
            await record_tile_access("user1", "slide1", 3, cache_hit=False)
        details = mock_log.call_args.kwargs["details"]
        assert details["cache_hit"] is False

    @pytest.mark.asyncio
    async def test_first_access_includes_cache_hit_true(self):
        """cache_hit=True must be forwarded to audit details."""
        mock_log = AsyncMock()
        with patch("services.tile_audit.log_audit_event", mock_log):
            await record_tile_access("user1", "slide1", 3, cache_hit=True)
        details = mock_log.call_args.kwargs["details"]
        assert details["cache_hit"] is True


class TestDeduplication:
    """Test that repeated accesses within the TTL window are deduplicated."""

    @pytest.mark.asyncio
    async def test_duplicate_same_zoom_returns_false(self):
        """Second access for same (user, slide, date) must return False."""
        await record_tile_access("user1", "slide1", 5)
        result = await record_tile_access("user1", "slide1", 5)
        assert result is False

    @pytest.mark.asyncio
    async def test_duplicate_different_zoom_returns_false(self):
        """Second access with different zoom level is still deduplicated."""
        await record_tile_access("user1", "slide1", 5)
        result = await record_tile_access("user1", "slide1", 10)
        assert result is False

    @pytest.mark.asyncio
    async def test_duplicate_does_not_log_again(self):
        """log_audit_event must be called exactly once for duplicate accesses."""
        mock_log = AsyncMock()
        with patch("services.tile_audit.log_audit_event", mock_log):
            await record_tile_access("user1", "slide1", 5)
            await record_tile_access("user1", "slide1", 5)
            await record_tile_access("user1", "slide1", 7)
        mock_log.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dedup_store_not_grown_on_duplicate(self):
        """Dedup store must contain exactly one entry after repeated accesses."""
        await record_tile_access("user1", "slide1", 5)
        await record_tile_access("user1", "slide1", 5)
        assert len(_dedup_store) == 1


class TestIsolation:
    """Test that different (user, slide, date) combinations are independent."""

    @pytest.mark.asyncio
    async def test_different_slide_not_deduplicated(self):
        """Different slide for same user must emit a separate event."""
        await record_tile_access("user1", "slide1", 5)
        result = await record_tile_access("user1", "slide2", 5)
        assert result is True

    @pytest.mark.asyncio
    async def test_different_user_not_deduplicated(self):
        """Same slide for different user must emit a separate event."""
        await record_tile_access("user1", "slide1", 5)
        result = await record_tile_access("user2", "slide1", 5)
        assert result is True

    @pytest.mark.asyncio
    async def test_different_user_and_slide_both_log(self):
        """Two distinct users viewing two distinct slides: two events."""
        mock_log = AsyncMock()
        with patch("services.tile_audit.log_audit_event", mock_log):
            await record_tile_access("user1", "slide1", 5)
            await record_tile_access("user2", "slide2", 5)
        assert mock_log.await_count == 2

    @pytest.mark.asyncio
    async def test_dedup_store_contains_two_entries_for_two_pairs(self):
        """Two distinct (user, slide) pairs must produce two dedup entries."""
        await record_tile_access("user1", "slide1", 5)
        await record_tile_access("user2", "slide1", 5)
        assert len(_dedup_store) == 2


class TestTTLExpiry:
    """Test that expired dedup entries allow re-logging."""

    @pytest.mark.asyncio
    async def test_expired_entry_allows_relogging(self):
        """After a dedup entry expires, the next access must emit a new event."""
        import time

        # Insert a pre-expired entry directly
        dedup_key = f"user1:slide1:{__import__('datetime').date.today().isoformat()}"
        _dedup_store[dedup_key] = time.monotonic() - 1  # expired 1 second ago

        result = await record_tile_access("user1", "slide1", 5)
        assert result is True


class TestAuditUnavailable:
    """Test graceful degradation when auth.audit is not importable."""

    @pytest.mark.asyncio
    async def test_returns_true_when_log_audit_event_is_none(self):
        """record_tile_access must still return True when log_audit_event is None
        (simulates environments where auth.audit could not be imported).
        """
        with patch("services.tile_audit.log_audit_event", None):
            result = await record_tile_access("user1", "slide1", 5)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_when_audit_raises_exception(self):
        """record_tile_access must still return True if log_audit_event raises."""
        mock_log = AsyncMock(side_effect=RuntimeError("DB connection refused"))
        with patch("services.tile_audit.log_audit_event", mock_log):
            result = await record_tile_access("user1", "slide1", 5)

        assert result is True
