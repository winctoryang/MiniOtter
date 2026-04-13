"""WebSocket endpoint for real-time agent event streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from .event_bus import EventBus

logger = logging.getLogger(__name__)


async def websocket_stream(websocket: WebSocket, event_bus: EventBus) -> None:
    await websocket.accept()
    session_id = websocket.query_params.get("session_id", "default")
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1000)
    event_bus.subscribe(session_id, queue)

    try:
        while True:
            event = await queue.get()
            await websocket.send_json(_clean_event(event))
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
    except Exception:
        logger.exception("WebSocket error for session %s", session_id)
    finally:
        event_bus.unsubscribe(session_id, queue)


def _clean_event(event: dict[str, Any]) -> dict[str, Any]:
    clean = {}
    for k, v in event.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict):
            clean[k] = _clean_event(v)
        else:
            try:
                json.dumps(v)
                clean[k] = v
            except (TypeError, ValueError):
                clean[k] = str(v)
    return clean
