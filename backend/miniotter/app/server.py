"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..agents.registry import AgentRegistry
from ..config import AppConfig, load_config
from .event_bus import EventBus
from .routes import chat, config as config_routes, health, tasks

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg: AppConfig = app.state.config
    logger.info("MiniOtter 启动中... host=%s port=%d", cfg.server.host, cfg.server.port)
    app.state.event_bus = EventBus()
    app.state.task_store = {}
    app.state.agent_registry = AgentRegistry(config=cfg)
    yield
    logger.info("MiniOtter 关闭中...")


def create_app(config: AppConfig | None = None) -> FastAPI:
    if config is None:
        config = load_config()

    app = FastAPI(title="MiniOtter", version="0.1.0", lifespan=lifespan)
    app.state.config = config

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(config_routes.router, prefix="/api")
    app.include_router(health.router, prefix="/api")

    @app.websocket("/ws/stream")
    async def ws_endpoint(websocket: WebSocket):
        await websocket.accept()
        session_id = websocket.query_params.get("session_id", "default")
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1000)
        app.state.event_bus.subscribe(session_id, queue)
        try:
            while True:
                event = await queue.get()
                await websocket.send_json(_clean_event(event))
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected for session %s", session_id)
        except Exception:
            logger.exception("WebSocket error for session %s", session_id)
        finally:
            app.state.event_bus.unsubscribe(session_id, queue)

    if STATIC_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = STATIC_DIR / full_path
            if file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(STATIC_DIR / "index.html"))

    return app


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
