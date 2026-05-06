"""
In-process WorkflowEvent broadcaster — fan-out from emit sites to connected
WebSocket clients.

Used by:
- `WebSocketWorkflowHook` (the WorkflowHook Protocol implementer that
  publishes to this broadcaster from any emit site in the codebase)
- `routes/ws.py:events_websocket` (the FastAPI endpoint that subscribes
  WebSockets to the broadcaster)

Design
------
- Process-wide singleton — `get_broadcaster()`.
- Subscribe / unsubscribe takes a `WebSocket` reference; `publish` fans an
  event payload (dict) to every subscriber that hasn't been removed yet.
- Failures on individual sockets are caught and logged; one slow / dead
  client cannot block other subscribers.
- No persistence — clients that connect AFTER an event was emitted miss
  it. WebSocket consumers are expected to refetch state from the REST
  API on connect (the events are deltas, not the source of truth).
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WorkflowEventBroadcaster:
    """Hold subscriber WebSockets and fan published events to all of them."""

    def __init__(self) -> None:
        self._subscribers: set["WebSocket"] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self, ws: "WebSocket") -> None:
        async with self._lock:
            self._subscribers.add(ws)
        logger.debug(
            "WorkflowEventBroadcaster: +1 subscriber (total=%d)",
            len(self._subscribers),
        )

    async def unsubscribe(self, ws: "WebSocket") -> None:
        async with self._lock:
            self._subscribers.discard(ws)
        logger.debug(
            "WorkflowEventBroadcaster: -1 subscriber (total=%d)",
            len(self._subscribers),
        )

    async def publish(self, payload: Dict[str, Any]) -> int:
        """Send `payload` as JSON to every subscriber. Returns delivery count.

        Drops broken subscribers silently (the WebSocket route is
        responsible for unsubscribing on its own disconnect path; this is
        a best-effort cleanup for sockets that died mid-write).
        """
        async with self._lock:
            snapshot = list(self._subscribers)

        delivered = 0
        broken: list = []
        for ws in snapshot:
            try:
                await ws.send_json(payload)
                delivered += 1
            except Exception as e:
                logger.debug("WorkflowEventBroadcaster: drop broken subscriber: %s", e)
                broken.append(ws)

        if broken:
            async with self._lock:
                for ws in broken:
                    self._subscribers.discard(ws)

        return delivered

    def subscriber_count(self) -> int:
        return len(self._subscribers)


_singleton: Optional[WorkflowEventBroadcaster] = None


def get_broadcaster() -> WorkflowEventBroadcaster:
    """Return the process-wide WorkflowEventBroadcaster singleton."""
    global _singleton
    if _singleton is None:
        _singleton = WorkflowEventBroadcaster()
    return _singleton


def reset_broadcaster() -> None:
    """Test helper — drop the singleton (next get_broadcaster() rebuilds it)."""
    global _singleton
    _singleton = None


__all__ = ["WorkflowEventBroadcaster", "get_broadcaster", "reset_broadcaster"]
