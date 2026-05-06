"""Quick interactive smoke test (NOT a pytest) — connect to /ws/events,
trigger an annotation event, observe it arrive on the WS.

Usage (against the running dev backend on :8000):
    python tests/smoke_ws_events.py
"""

from __future__ import annotations

import asyncio
import json

import httpx
import websockets


async def listen(ws_url: str, stop_after_seconds: float = 8.0):
    received = []
    async with websockets.connect(ws_url) as ws:
        print(f"[WS] connected to {ws_url}")
        try:
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=stop_after_seconds)
                except TimeoutError:
                    break
                received.append(raw)
                print(f"[WS] recv: {raw}")
        except Exception as e:
            print(f"[WS] recv error: {e}")
    return received


async def trigger_event():
    """Hit the export endpoint to fire a REPORT_SIGNED event."""
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=5.0) as client:
        r = await client.post("/api/v1/exports/dicom/abcdef012345?anonymize=true")
        print(f"[HTTP] export POST -> {r.status_code}: {r.text[:200]}")


async def main():
    ws_url = "ws://localhost:8000/api/v1/ws/events"
    listener_task = asyncio.create_task(listen(ws_url, stop_after_seconds=4.0))

    await asyncio.sleep(1.5)
    await trigger_event()

    received = await listener_task
    print(f"\n[summary] received {len(received)} frames")
    for i, frame in enumerate(received):
        try:
            data = json.loads(frame)
            print(f"  {i}: type={data.get('type', data.get('event_type'))}")
        except Exception:
            print(f"  {i}: {frame[:100]}")


if __name__ == "__main__":
    asyncio.run(main())
