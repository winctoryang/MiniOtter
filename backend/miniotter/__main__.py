"""Entry point: python -m miniotter

启动方式:
  桌面应用: python -m miniotter          (默认，打开桌面窗口)
  仅后端:   python -m miniotter --server (仅启动 HTTP 服务，不打开窗口)
  开发模式: python -m miniotter --dev    (仅后端，前端用 npm run dev 单独启动)
"""

import argparse
import logging
import threading

import uvicorn

from .config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="MiniOtter")
    parser.add_argument("--server", action="store_true", help="仅启动后端服务，不打开桌面窗口")
    parser.add_argument("--dev", action="store_true", help="开发模式：仅后端，前端用 npm run dev")
    args = parser.parse_args()

    config = load_config()
    from .app.server import create_app
    app = create_app(config)

    if args.server or args.dev:
        # 仅后端模式
        uvicorn.run(app, host=config.server.host, port=config.server.port)
    else:
        # 桌面应用模式：后台线程跑 FastAPI，主线程开 pywebview 窗口
        server_thread = threading.Thread(
            target=uvicorn.run,
            kwargs={"app": app, "host": config.server.host, "port": config.server.port, "log_level": "warning"},
            daemon=True,
        )
        server_thread.start()

        import time
        time.sleep(1)  # 等待服务启动

        import webview
        url = f"http://{config.server.host}:{config.server.port}"
        logger.info("打开桌面窗口: %s", url)
        webview.create_window("MiniOtter", url, width=1200, height=800)
        webview.start()


if __name__ == "__main__":
    main()
