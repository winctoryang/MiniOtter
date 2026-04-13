"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..agents.registry import AgentRegistry
from ..config import AppConfig, load_config
from .event_bus import EventBus
from .routes import chat, config as config_routes, health, tasks
from .ws import websocket_stream

logger = logging.getLogger(__name__)

# 前端构建产物目录
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

    # API routes
    app.include_router(chat.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(config_routes.router, prefix="/api")
    app.include_router(health.router, prefix="/api")

    # WebSocket
    @app.websocket("/ws/stream")
    async def ws_endpoint(websocket: WebSocket):
        await websocket_stream(websocket, app.state.event_bus)

    # 前端静态文件（构建后）
    if STATIC_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """SPA fallback: 所有非 API/WS 请求返回 index.html"""
            file_path = STATIC_DIR / full_path
            if file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(STATIC_DIR / "index.html"))

    return app
