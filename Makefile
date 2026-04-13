.PHONY: install build start dev

# 安装所有依赖
install:
	uv sync
	cd frontend && npm install

# 构建前端到 backend/miniotter/static
build:
	cd frontend && npm run build

# 启动桌面应用（需要先 build）
start:
	cd backend && uv run python -m miniotter

# 开发模式：后端 + 前端热更新（两个终端分别执行）
dev-backend:
	cd backend && uv run python -m miniotter --dev

dev-frontend:
	cd frontend && npm run dev
