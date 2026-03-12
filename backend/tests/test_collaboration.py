"""
Collaboration Feature Tests

Tests for sharing (Issue #13), WebSocket annotations (Issue #14),
annotation merge (Issue #35), and WebSocket security (Issue #209).
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocketDisconnect

from services.annotation_merge import AnnotationMergeService, MergeStrategy
from services.sharing import SharingService

# ============================================
# SharingService Tests
# ============================================


class TestSharingService:
    """Tests for SharingService (Issue #13)."""

    def setup_method(self):
        self.service = SharingService()

    def test_create_share_returns_valid_token_and_url(self):
        """Create share returns a ShareLink with token and URL."""
        link = self.service.create_share(slide_id="slide_001", permission="view")

        assert link.token is not None
        assert len(link.token) > 0
        assert link.url == f"/share/{link.token}"
        assert link.slide_id == "slide_001"
        assert link.permission == "view"
        assert link.expires_at is not None
        assert link.revoked is False

    def test_validate_share_returns_correct_link(self):
        """Validate share returns the correct ShareLink for a valid token."""
        link = self.service.create_share(slide_id="slide_002", permission="annotate")
        result = self.service.validate_share(link.token)

        assert result is not None
        assert result.token == link.token
        assert result.slide_id == "slide_002"
        assert result.permission == "annotate"

    def test_expired_share_returns_none(self):
        """Validate returns None for an expired share token."""
        link = self.service.create_share(slide_id="slide_003", permission="view", expires_hours=1)
        # Manually set expires_at to the past
        link.expires_at = datetime.now(UTC) - timedelta(hours=1)

        result = self.service.validate_share(link.token)
        assert result is None

    def test_revoked_share_returns_none(self):
        """Validate returns None for a revoked share token."""
        link = self.service.create_share(slide_id="slide_004", permission="view")
        self.service.revoke_share(link.token)

        result = self.service.validate_share(link.token)
        assert result is None

    def test_list_shares_filters_by_slide_id(self):
        """List shares correctly filters by slide_id."""
        self.service.create_share(slide_id="slide_A")
        self.service.create_share(slide_id="slide_B")
        self.service.create_share(slide_id="slide_A")

        results = self.service.list_shares(slide_id="slide_A")
        assert len(results) == 2
        for link in results:
            assert link.slide_id == "slide_A"

    def test_revoke_nonexistent_token_returns_false(self):
        """Revoke returns False for a token that does not exist."""
        result = self.service.revoke_share("nonexistent_token")
        assert result is False

    def test_validate_nonexistent_token_returns_none(self):
        """Validate returns None for a token that does not exist."""
        result = self.service.validate_share("nonexistent_token")
        assert result is None

    def test_create_share_no_expiration(self):
        """Create share with expires_hours=0 produces no expiration."""
        link = self.service.create_share(slide_id="slide_005", expires_hours=0)
        assert link.expires_at is None

        # Should validate successfully
        result = self.service.validate_share(link.token)
        assert result is not None

    def test_validate_increments_access_count(self):
        """Each successful validation increments the access counter."""
        link = self.service.create_share(slide_id="slide_006")
        assert link.access_count == 0

        self.service.validate_share(link.token)
        assert link.access_count == 1

        self.service.validate_share(link.token)
        assert link.access_count == 2

    def test_list_shares_excludes_revoked(self):
        """List shares does not return revoked links."""
        link_a = self.service.create_share(slide_id="slide_X")
        self.service.create_share(slide_id="slide_X")
        self.service.revoke_share(link_a.token)

        results = self.service.list_shares(slide_id="slide_X")
        assert len(results) == 1

    def test_create_share_with_created_by(self):
        """Created_by is stored on the share link."""
        link = self.service.create_share(slide_id="s1", created_by="user_42")
        assert link.created_by == "user_42"

        results = self.service.list_shares(created_by="user_42")
        assert len(results) == 1
        assert results[0].created_by == "user_42"


# ============================================
# ConnectionManager Tests
# ============================================


class TestConnectionManager:
    """Tests for WebSocket ConnectionManager (Issue #14)."""

    def setup_method(self):
        from routes.ws import ConnectionManager

        self.manager = ConnectionManager()

    def _make_mock_ws(self):
        """Create a mock WebSocket that can be used in sets (hashable)."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        # MagicMock is hashable by default (uses id)
        return ws

    @pytest.mark.asyncio
    async def test_connect_adds_to_active_connections(self):
        """Connect registers the WebSocket in active_connections."""
        ws = self._make_mock_ws()
        await self.manager.connect(ws, "slide_1", {"id": "user1", "name": "User 1"})

        assert "slide_1" in self.manager.active_connections
        assert ws in self.manager.active_connections["slide_1"]
        assert len(self.manager.active_connections["slide_1"]) == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_active_connections(self):
        """Disconnect removes the WebSocket from active_connections."""
        ws = self._make_mock_ws()
        await self.manager.connect(ws, "slide_2", {"id": "user1", "name": "User 1"})
        assert ws in self.manager.active_connections["slide_2"]

        await self.manager.disconnect(ws, "slide_2")
        # After disconnect, the set should be cleaned up
        assert "slide_2" not in self.manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_except_excluded(self):
        """Broadcast sends message to all connections except the excluded one."""
        ws1 = self._make_mock_ws()
        ws2 = self._make_mock_ws()
        ws3 = self._make_mock_ws()

        await self.manager.connect(ws1, "slide_3", {"id": "u1"})
        await self.manager.connect(ws2, "slide_3", {"id": "u2"})
        await self.manager.connect(ws3, "slide_3", {"id": "u3"})

        # Reset mocks after connect (which triggers broadcasts)
        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()
        ws3.send_json.reset_mock()

        msg = {"type": "test", "data": "hello"}
        await self.manager.broadcast("slide_3", msg, exclude=ws1)

        # ws1 excluded, ws2 and ws3 should receive
        ws1.send_json.assert_not_called()
        ws2.send_json.assert_called_once_with(msg)
        ws3.send_json.assert_called_once_with(msg)

    @pytest.mark.asyncio
    async def test_broadcast_no_exclude_sends_to_all(self):
        """Broadcast without exclude sends to all connections."""
        ws1 = self._make_mock_ws()
        ws2 = self._make_mock_ws()

        await self.manager.connect(ws1, "slide_4", {"id": "u1"})
        await self.manager.connect(ws2, "slide_4", {"id": "u2"})

        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()

        msg = {"type": "test"}
        await self.manager.broadcast("slide_4", msg)

        ws1.send_json.assert_called_once_with(msg)
        ws2.send_json.assert_called_once_with(msg)

    @pytest.mark.asyncio
    async def test_connect_broadcasts_user_joined(self):
        """When a second user connects, the first receives a user_joined message."""
        ws1 = self._make_mock_ws()
        ws2 = self._make_mock_ws()

        await self.manager.connect(ws1, "slide_5", {"id": "u1", "name": "User 1"})
        ws1.send_json.reset_mock()

        await self.manager.connect(ws2, "slide_5", {"id": "u2", "name": "User 2"})

        # ws1 should have received user_joined
        assert ws1.send_json.call_count == 1
        call_args = ws1.send_json.call_args[0][0]
        assert call_args["type"] == "user_joined"
        assert call_args["user"]["id"] == "u2"
        assert call_args["active_users"] == 2

    @pytest.mark.asyncio
    async def test_get_active_users(self):
        """get_active_users returns user info for all connected users."""
        ws1 = self._make_mock_ws()
        ws2 = self._make_mock_ws()

        await self.manager.connect(ws1, "slide_6", {"id": "u1", "name": "Alice"})
        await self.manager.connect(ws2, "slide_6", {"id": "u2", "name": "Bob"})

        users = self.manager.get_active_users("slide_6")
        assert len(users) == 2
        names = {u["name"] for u in users}
        assert names == {"Alice", "Bob"}

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_failure(self):
        """Broadcast silently handles send failures on broken connections."""
        ws1 = self._make_mock_ws()
        ws2 = self._make_mock_ws()
        ws2.send_json = AsyncMock(side_effect=RuntimeError("connection closed"))

        await self.manager.connect(ws1, "slide_7", {"id": "u1"})
        await self.manager.connect(ws2, "slide_7", {"id": "u2"})

        ws1.send_json.reset_mock()

        # Should not raise despite ws2 failing
        msg = {"type": "test"}
        await self.manager.broadcast("slide_7", msg)

        ws1.send_json.assert_called_once_with(msg)


# ============================================
# AnnotationMergeService Tests
# ============================================


class TestAnnotationMergeService:
    """Tests for AnnotationMergeService (Issue #35)."""

    def setup_method(self):
        self.service = AnnotationMergeService(iou_threshold=0.3)

    def _make_annotation(self, x1, y1, x2, y2, created_by="user_a", created_at=None, label=None):
        """Helper to build an annotation dict with a Polygon geometry."""
        return {
            "id": f"{created_by}_{x1}_{y1}",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]],
            },
            "created_by": created_by,
            "created_at": created_at or datetime.now(UTC).isoformat(),
            "label": label,
        }

    def test_union_merge_keeps_all_annotations(self):
        """Union strategy keeps all annotations regardless of conflicts."""
        set_a = [self._make_annotation(0, 0, 10, 10, "user_a")]
        set_b = [self._make_annotation(100, 100, 110, 110, "user_b")]

        result = self.service.merge([set_a, set_b], MergeStrategy.UNION)

        assert result.strategy == "union"
        assert result.total_input == 2
        assert result.merged_count == 2
        assert len(result.merged_annotations) == 2

    def test_last_write_wins_picks_most_recent(self):
        """Last-write-wins keeps the annotation with the later created_at."""
        # Overlapping annotations from different users
        old = self._make_annotation(0, 0, 10, 10, "user_a", "2024-01-01T00:00:00")
        new = self._make_annotation(2, 2, 12, 12, "user_b", "2024-06-01T00:00:00")

        result = self.service.merge([[old], [new]], MergeStrategy.LAST_WRITE_WINS)

        assert result.strategy == "last_write_wins"
        assert result.conflicts_found >= 1
        # The newer annotation should survive
        assert result.merged_count == 1
        assert result.merged_annotations[0]["created_by"] == "user_b"

    def test_conflict_detection_finds_overlapping_annotations(self):
        """Overlapping annotations from different users are detected as conflicts."""
        # IoU for (0,0)-(10,10) and (3,3)-(13,13): intersection=49, union=151, IoU~0.324 > 0.3
        a = self._make_annotation(0, 0, 10, 10, "user_a")
        b = self._make_annotation(3, 3, 13, 13, "user_b")

        result = self.service.merge([[a], [b]], MergeStrategy.UNION)

        assert result.conflicts_found >= 1
        conflict = result.conflicts[0]
        assert conflict.overlap_iou > 0

    def test_no_conflicts_all_pass_through(self):
        """Non-overlapping annotations produce no conflicts."""
        a = self._make_annotation(0, 0, 10, 10, "user_a")
        b = self._make_annotation(100, 100, 110, 110, "user_b")

        result = self.service.merge([[a], [b]], MergeStrategy.UNION)

        assert result.conflicts_found == 0
        assert result.merged_count == 2

    def test_iou_computation_overlapping_boxes(self):
        """IoU is computed correctly for known overlapping boxes."""
        # Box A: (0,0)-(10,10), area 100
        # Box B: (5,5)-(15,15), area 100
        # Intersection: (5,5)-(10,10), area 25
        # Union: 200-25 = 175, expected IoU ~ 0.1429
        geom_a = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
        }
        geom_b = {
            "type": "Polygon",
            "coordinates": [[[5, 5], [15, 5], [15, 15], [5, 15], [5, 5]]],
        }

        iou = self.service.compute_iou(geom_a, geom_b)
        expected = 25.0 / 175.0
        assert abs(iou - expected) < 0.001

    def test_iou_non_overlapping_is_zero(self):
        """IoU is 0 for non-overlapping boxes."""
        geom_a = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
        }
        geom_b = {
            "type": "Polygon",
            "coordinates": [[[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]]],
        }

        iou = self.service.compute_iou(geom_a, geom_b)
        assert iou == 0.0

    def test_iou_identical_boxes_is_one(self):
        """IoU is 1.0 for identical boxes."""
        geom = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
        }

        iou = self.service.compute_iou(geom, geom)
        assert abs(iou - 1.0) < 0.001

    def test_iou_missing_geometry_returns_zero(self):
        """IoU returns 0 when geometry is missing or invalid."""
        geom_a = {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10]]]}
        geom_b = {}

        iou = self.service.compute_iou(geom_a, geom_b)
        assert iou == 0.0

    def test_same_user_annotations_not_conflicting(self):
        """Overlapping annotations from the same user are not flagged as conflicts."""
        a = self._make_annotation(0, 0, 10, 10, "user_a")
        b = self._make_annotation(5, 5, 15, 15, "user_a")

        result = self.service.merge([[a, b]], MergeStrategy.UNION)
        assert result.conflicts_found == 0

    def test_intersection_strategy_keeps_only_conflicting(self):
        """Intersection strategy keeps only annotations that overlap with others."""
        overlap_a = self._make_annotation(0, 0, 10, 10, "user_a")
        overlap_b = self._make_annotation(2, 2, 12, 12, "user_b")
        isolated = self._make_annotation(100, 100, 110, 110, "user_c")

        result = self.service.merge(
            [[overlap_a], [overlap_b], [isolated]], MergeStrategy.INTERSECTION
        )

        # Only the overlapping pair should remain
        assert result.merged_count == 2
        created_bys = {a["created_by"] for a in result.merged_annotations}
        assert "user_c" not in created_bys

    def test_merge_empty_sets(self):
        """Merging empty annotation sets produces empty result."""
        result = self.service.merge([], MergeStrategy.UNION)

        assert result.total_input == 0
        assert result.merged_count == 0
        assert result.conflicts_found == 0

    def test_merge_result_has_processing_time(self):
        """MergeResult includes processing_time_ms."""
        a = self._make_annotation(0, 0, 10, 10, "user_a")
        result = self.service.merge([[a]], MergeStrategy.UNION)

        assert result.processing_time_ms >= 0


# ============================================
# WebSocket Security Tests (Issue #209)
# ============================================

import json as _json
import time

from routes.ws import (
    WS_CLOSE_RATE_LIMIT,
    WS_MAX_MESSAGE_SIZE,
    _RateLimiter,
    _resolve_user_from_token,
    slide_websocket,
)


class TestRateLimiter:
    """Tests for the per-connection sliding-window rate limiter."""

    def test_allows_messages_within_limit(self):
        """Messages within the rate limit are accepted."""
        rl = _RateLimiter(max_messages=5, window=60.0)
        for _ in range(5):
            assert rl.is_allowed() is True

    def test_blocks_message_exceeding_limit(self):
        """The (max+1)th message within the window is rejected."""
        rl = _RateLimiter(max_messages=3, window=60.0)
        for _ in range(3):
            rl.is_allowed()
        assert rl.is_allowed() is False

    def test_window_expiry_resets_count(self):
        """After the window expires, new messages are accepted again."""
        rl = _RateLimiter(max_messages=2, window=0.05)
        rl.is_allowed()
        rl.is_allowed()
        assert rl.is_allowed() is False  # window full

        time.sleep(0.06)  # let the window expire
        assert rl.is_allowed() is True  # fresh window


class TestResolveUserFromToken:
    """Tests for JWT resolution helper _resolve_user_from_token."""

    @pytest.mark.asyncio
    async def test_auth_disabled_returns_anonymous(self):
        """When AUTH_ENABLED=false, any token (or None) yields anonymous user."""
        with patch("auth.AUTH_ENABLED", False):
            user = await _resolve_user_from_token(None)

        assert user is not None
        assert user["name"] == "anonymous"
        assert "ADMIN_TECHNIQUE" in user["roles"]

    @pytest.mark.asyncio
    async def test_auth_enabled_missing_token_returns_none(self):
        """When AUTH_ENABLED=true and no token is provided, returns None."""
        with patch("auth.AUTH_ENABLED", True):
            user = await _resolve_user_from_token(None)

        assert user is None

    @pytest.mark.asyncio
    async def test_auth_enabled_invalid_token_returns_none(self):
        """When AUTH_ENABLED=true and token is invalid, returns None."""
        # jwt_validator is imported lazily inside _resolve_user_from_token.
        # Inject a fake module so we don't need python-jose installed in CI.
        import sys
        import types

        fake_jv = types.ModuleType("auth.jwt_validator")
        fake_jv.validate_token = AsyncMock(side_effect=ValueError("bad token"))

        with (
            patch("auth.AUTH_ENABLED", True),
            patch.dict(sys.modules, {"auth.jwt_validator": fake_jv}),
        ):
            user = await _resolve_user_from_token("invalid.jwt.token")

        assert user is None

    @pytest.mark.asyncio
    async def test_auth_enabled_valid_token_returns_user(self):
        """When AUTH_ENABLED=true and token is valid, returns user info dict."""
        import sys
        import types

        fake_claims = {
            "sub": "user-123",
            "preferred_username": "dr.smith",
            "email": "dr.smith@hospital.be",
            "realm_access": {"roles": ["MEDECIN"]},
        }

        fake_jv = types.ModuleType("auth.jwt_validator")
        fake_jv.validate_token = AsyncMock(return_value=fake_claims)

        with (
            patch("auth.AUTH_ENABLED", True),
            patch.dict(sys.modules, {"auth.jwt_validator": fake_jv}),
        ):
            user = await _resolve_user_from_token("valid.jwt.token")

        assert user is not None
        assert user["id"] == "user-123"
        assert user["name"] == "dr.smith"
        assert user["email"] == "dr.smith@hospital.be"
        assert "MEDECIN" in user["roles"]


class TestWebSocketSecurityEndpoint:
    """Integration tests for WebSocket security (close codes, size limits)."""

    def _make_mock_ws(self, token=None):
        """Create a mock WebSocket with query_params and close tracking."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()
        ws.client = MagicMock()
        ws.client.host = "127.0.0.1"
        ws.query_params = {"token": token} if token else {}
        return ws

    @pytest.mark.asyncio
    async def test_unauthenticated_connection_closes_4001(self):
        """Connection without a valid token is closed with code 4001."""
        ws = self._make_mock_ws(token=None)

        with patch("auth.AUTH_ENABLED", True):
            await slide_websocket(ws, "slide_auth_test")

        ws.close.assert_called_once_with(code=4001)
        ws.accept.assert_not_called()

    @pytest.mark.asyncio
    async def test_oversized_message_is_dropped_connection_stays(self):
        """A message exceeding WS_MAX_MESSAGE_SIZE is dropped; connection remains open."""
        import routes.ws as ws_module

        oversized_payload = b"x" * (WS_MAX_MESSAGE_SIZE + 1)
        normal_payload = _json.dumps({"type": "cursor_move", "position": {"x": 1, "y": 1}}).encode()

        call_count = 0

        async def _receive_bytes():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return oversized_payload
            if call_count == 2:
                return normal_payload
            raise WebSocketDisconnect

        ws = self._make_mock_ws(token=None)
        ws.receive_bytes = _receive_bytes

        original_manager = ws_module.manager
        ws_module.manager = ws_module.ConnectionManager()
        try:
            with patch("auth.AUTH_ENABLED", False):
                await slide_websocket(ws, "slide_size_test")
        finally:
            ws_module.manager = original_manager

        # Connection should NOT have been closed with an error code
        for call in ws.close.call_args_list:
            assert call.kwargs.get("code") not in (4001, 4002), f"Unexpected close code: {call}"

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_closes_4002(self):
        """Exceeding the rate limit closes the connection with code 4002."""
        import routes.ws as ws_module

        msg = _json.dumps({"type": "cursor_move", "position": {"x": 0, "y": 0}}).encode()

        async def _receive_bytes():
            return msg

        ws = self._make_mock_ws(token=None)
        ws.receive_bytes = _receive_bytes

        limiter = MagicMock()
        # First call allowed so connect succeeds; subsequent calls denied
        limiter.is_allowed.side_effect = [True] + [False] * 200

        original_manager = ws_module.manager
        ws_module.manager = ws_module.ConnectionManager()
        try:
            with (
                patch("auth.AUTH_ENABLED", False),
                patch("routes.ws._RateLimiter", return_value=limiter),
            ):
                await slide_websocket(ws, "slide_rate_test")
        finally:
            ws_module.manager = original_manager

        ws.close.assert_called_with(code=WS_CLOSE_RATE_LIMIT)
