"""
WebSocket Routes - Real-time collaborative annotations.

Provides a WebSocket endpoint per slide for broadcasting annotation
changes, cursor positions, and region locks between connected users.
Also exposes a REST endpoint for querying active presence on a slide.

Security:
    - JWT validation on connect (token query param, respects AUTH_ENABLED flag)
    - Message size limit (WS_MAX_MESSAGE_SIZE env var, default 64 KB)
    - Rate limiting (100 messages/minute per connection)
    - Close code 4001: authentication failure
    - Close code 4002: rate limit exceeded
"""

import json
import logging
import os
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WS_MAX_MESSAGE_SIZE: int = int(os.getenv("WS_MAX_MESSAGE_SIZE", str(64 * 1024)))  # 64 KB
_RATE_LIMIT_MAX: int = 100  # max messages per window
_RATE_LIMIT_WINDOW: float = 60.0  # seconds


# ---------------------------------------------------------------------------
# WebSocket close codes (application-level)
# ---------------------------------------------------------------------------

WS_CLOSE_AUTH_FAILURE = 4001
WS_CLOSE_RATE_LIMIT = 4002


# ---------------------------------------------------------------------------
# JWT resolution helper
# ---------------------------------------------------------------------------


async def _resolve_user_from_token(token: str | None) -> dict | None:
    """
    Validate a JWT token and return user info, or None on failure.

    When AUTH_ENABLED=false, skip validation and return anonymous user.
    When AUTH_ENABLED=true, require a valid token; return None if invalid.

    References:
        - auth/dependencies.py: get_current_user() for HTTP routes
        - auth/jwt_validator.py: validate_token()
        - auth/__init__.py: AUTH_ENABLED flag
    """
    from auth import AUTH_ENABLED

    if not AUTH_ENABLED:
        return {"id": "anonymous", "name": "anonymous", "roles": ["ADMIN_TECHNIQUE"]}

    if not token:
        return None

    try:
        from auth.config import get_oidc_config
        from auth.jwt_validator import validate_token

        claims = await validate_token(token)

        # Extract roles using the same logic as dependencies.py
        config = get_oidc_config()
        parts = config.role_claim.split(".")
        value = claims
        for part in parts:
            value = value.get(part, []) if isinstance(value, dict) else []
        valid_roles = {"LECTURE_SEULE", "INFIRMIER", "MEDECIN", "ADMIN_TECHNIQUE"}
        roles = [r for r in value if r in valid_roles] if isinstance(value, list) else []

        return {
            "id": claims.get("sub", "unknown"),
            "name": claims.get("preferred_username", claims.get("sub", "unknown")),
            "email": claims.get("email"),
            "roles": roles,
        }
    except Exception as exc:
        logger.warning("WebSocket JWT validation failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Per-connection rate limiter
# ---------------------------------------------------------------------------


class _RateLimiter:
    """Sliding-window rate limiter for a single WebSocket connection."""

    def __init__(self, max_messages: int = _RATE_LIMIT_MAX, window: float = _RATE_LIMIT_WINDOW):
        self._max = max_messages
        self._window = window
        self._timestamps: list[float] = []

    def is_allowed(self) -> bool:
        """Return True if the message is within the rate limit, False otherwise."""
        now = time.monotonic()
        cutoff = now - self._window
        # Evict old entries
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        if len(self._timestamps) >= self._max:
            return False
        self._timestamps.append(now)
        return True


# ---------------------------------------------------------------------------
# ConnectionManager
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Manage WebSocket connections per slide.

    Tracks active connections grouped by slide_id and associated
    user metadata. Broadcasts messages to all connections for a
    slide, optionally excluding the sender.
    """

    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.user_info: dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, slide_id: str, user_info: dict | None = None):
        """Accept a WebSocket connection and register it for a slide."""
        await websocket.accept()
        if slide_id not in self.active_connections:
            self.active_connections[slide_id] = set()
        self.active_connections[slide_id].add(websocket)
        self.user_info[websocket] = user_info or {}

        # Broadcast user joined to other connections
        await self.broadcast(
            slide_id,
            {
                "type": "user_joined",
                "user": user_info,
                "active_users": len(self.active_connections[slide_id]),
            },
            exclude=websocket,
        )

        logger.info(
            "WebSocket connected: slide=%s, user=%s, total=%d",
            slide_id,
            (user_info or {}).get("name", "anonymous"),
            len(self.active_connections[slide_id]),
        )

    async def disconnect(self, websocket: WebSocket, slide_id: str):
        """Remove a WebSocket connection and notify remaining users."""
        self.active_connections.get(slide_id, set()).discard(websocket)
        user = self.user_info.pop(websocket, {})

        # Clean up empty sets
        if slide_id in self.active_connections and not self.active_connections[slide_id]:
            del self.active_connections[slide_id]

        active_count = len(self.active_connections.get(slide_id, set()))
        await self.broadcast(
            slide_id,
            {
                "type": "user_left",
                "user": user,
                "active_users": active_count,
            },
        )

        logger.info(
            "WebSocket disconnected: slide=%s, user=%s, remaining=%d",
            slide_id,
            user.get("name", "anonymous"),
            active_count,
        )

    async def broadcast(self, slide_id: str, message: dict, exclude: WebSocket = None):
        """Send a JSON message to all connections for a slide.

        Silently ignores send failures on broken connections.
        """
        connections = self.active_connections.get(slide_id, set()).copy()
        for conn in connections:
            if conn != exclude:
                try:
                    await conn.send_json(message)
                except Exception:
                    logger.debug("Failed to send to connection on slide %s", slide_id)

    def get_active_users(self, slide_id: str) -> list[dict]:
        """Return list of user info dicts for a slide."""
        connections = self.active_connections.get(slide_id, set())
        return [self.user_info.get(c, {}) for c in connections]


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@router.websocket("/ws/slides/{slide_id}")
async def slide_websocket(websocket: WebSocket, slide_id: str):
    """WebSocket endpoint for real-time collaboration on a slide.

    Query params:
        token: JWT access token (required when AUTH_ENABLED=true)
        username: Display name override (ignored when AUTH_ENABLED=true)

    Security:
        - Validates JWT on connect; closes with 4001 on auth failure.
        - Enforces WS_MAX_MESSAGE_SIZE per message; oversized frames are
          silently dropped (the raw bytes are read to drain the socket).
        - Rate-limits to 100 messages/minute; closes with 4002 on excess.

    Message types (client -> server):
        - annotation_created: Broadcast new annotation to other users
        - annotation_updated: Broadcast annotation update
        - annotation_deleted: Broadcast annotation deletion
        - cursor_move: Broadcast cursor position
        - region_lock: Request region lock
        - region_unlock: Release region lock
    """
    token = websocket.query_params.get("token")
    user_info = await _resolve_user_from_token(token)

    if user_info is None:
        # Authentication required but token missing or invalid
        logger.warning(
            "WebSocket auth failure: slide=%s, ip=%s",
            slide_id,
            websocket.client.host if websocket.client else "unknown",
        )
        await websocket.close(code=WS_CLOSE_AUTH_FAILURE)
        return

    rate_limiter = _RateLimiter()

    await manager.connect(websocket, slide_id, user_info)
    try:
        while True:
            # Read raw bytes first so we can enforce the size limit before
            # attempting JSON parsing (avoids allocating a huge string).
            raw = await websocket.receive_bytes()

            if len(raw) > WS_MAX_MESSAGE_SIZE:
                logger.warning(
                    "WebSocket message too large: slide=%s, user=%s, size=%d, limit=%d",
                    slide_id,
                    user_info.get("name", "anonymous"),
                    len(raw),
                    WS_MAX_MESSAGE_SIZE,
                )
                # Drop oversized message; keep connection alive
                continue

            if not rate_limiter.is_allowed():
                logger.warning(
                    "WebSocket rate limit exceeded: slide=%s, user=%s",
                    slide_id,
                    user_info.get("name", "anonymous"),
                )
                await websocket.close(code=WS_CLOSE_RATE_LIMIT)
                return

            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.debug(
                    "WebSocket invalid JSON from user=%s on slide=%s",
                    user_info.get("name"),
                    slide_id,
                )
                continue

            msg_type = data.get("type", "")

            if msg_type == "annotation_created":
                await manager.broadcast(
                    slide_id,
                    {
                        "type": "annotation_created",
                        "annotation": data.get("annotation"),
                        "user": user_info,
                    },
                    exclude=websocket,
                )

            elif msg_type == "annotation_updated":
                await manager.broadcast(
                    slide_id,
                    {
                        "type": "annotation_updated",
                        "annotation": data.get("annotation"),
                        "user": user_info,
                    },
                    exclude=websocket,
                )

            elif msg_type == "annotation_deleted":
                await manager.broadcast(
                    slide_id,
                    {
                        "type": "annotation_deleted",
                        "annotation_id": data.get("annotation_id"),
                        "user": user_info,
                    },
                    exclude=websocket,
                )

            elif msg_type == "cursor_move":
                await manager.broadcast(
                    slide_id,
                    {
                        "type": "cursor_move",
                        "position": data.get("position"),
                        "user": user_info,
                    },
                    exclude=websocket,
                )

            elif msg_type == "region_lock":
                await manager.broadcast(
                    slide_id,
                    {
                        "type": "region_locked",
                        "region": data.get("region"),
                        "user": user_info,
                    },
                    exclude=websocket,
                )

            elif msg_type == "region_unlock":
                await manager.broadcast(
                    slide_id,
                    {
                        "type": "region_unlocked",
                        "region": data.get("region"),
                        "user": user_info,
                    },
                    exclude=websocket,
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket, slide_id)


# ---------------------------------------------------------------------------
# REST presence endpoint
# ---------------------------------------------------------------------------


@router.get("/api/ws/slides/{slide_id}/presence")
async def get_presence(slide_id: str):
    """Get active users for a slide.

    Returns the count and list of users currently connected via WebSocket.
    """
    users = manager.get_active_users(slide_id)
    return {
        "slide_id": slide_id,
        "active_users": len(users),
        "users": users,
    }
