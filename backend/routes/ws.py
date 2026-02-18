"""
WebSocket Routes - Real-time collaborative annotations.

Provides a WebSocket endpoint per slide for broadcasting annotation
changes, cursor positions, and region locks between connected users.
Also exposes a REST endpoint for querying active presence on a slide.
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


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


@router.websocket("/ws/slides/{slide_id}")
async def slide_websocket(websocket: WebSocket, slide_id: str):
    """WebSocket endpoint for real-time collaboration on a slide.

    Query params:
        username: Display name for the connecting user (default: "anonymous")

    Message types (client -> server):
        - annotation_created: Broadcast new annotation to other users
        - annotation_updated: Broadcast annotation update
        - annotation_deleted: Broadcast annotation deletion
        - cursor_move: Broadcast cursor position
        - region_lock: Request region lock
        - region_unlock: Release region lock
    """
    username = websocket.query_params.get("username", "anonymous")
    user_info = {"id": username, "name": username}

    await manager.connect(websocket, slide_id, user_info)
    try:
        while True:
            data = await websocket.receive_json()
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
