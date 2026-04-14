# MiniOtter

基于 GUI 的自动化 Agent 桌面应用，可以在 macOS 上通过截图理解屏幕内容，使用鼠标和键盘操作桌面应用程序完成用户任务。

一键启动，内置前后端，直接打开桌面窗口即可使用。

## 架构

```
用户输入任务
    ↓
┌─────────────┐
│  主 Agent    │  分析任务，路由到子 Agent
└──────┬──────┘
       ├──────────────────┐
       ↓                  ↓
┌─────────────┐    ┌─────────────┐
│  GUI Agent  │    │  文本 Agent  │
│  截图+a11y  │    │  bash+文件   │
│  鼠标+键盘  │    │  剪贴板      │
└─────────────┘    └─────────────┘
```

- **主 Agent** — 只负责任务分发，判断任务交给哪个子 Agent
- **GUI Agent** — 基于截图和 a11y tree，执行鼠标键盘操作（需要多模态 LLM）
- **文本 Agent** — 执行 bash 命令、读写文件等文本任务
- **扩展 Agent** — 预留可扩展

每个 Agent 都有独立的 ReAct Loop，互不影响。

## 技术栈

| 层 | 技术 |
|---|---|
| 桌面窗口 | pywebview（原生 WebKit 窗口） |
| 前端 | React 18 + TypeScript + Vite + Zustand |
| 后端 | Python + FastAPI + WebSocket |
| Agent 引擎 | 自定义 ReAct Loop |
| LLM | Claude / OpenAI（可配置） |
| macOS 平台 | screencapture + pyobjc (a11y) + pyautogui (输入) |

## LLM 配置

项目使用两套独立的 LLM：

| LLM | 用途 | 要求 |
|-----|------|------|
| 文本 LLM | 主 Agent 任务路由 + 文本 Agent | 普通文本模型即可 |
| 视觉 LLM | GUI Agent 看截图操作桌面 | 需要多模态（支持图片输入） |

API Key 通过应用内 Settings 页面配置，持久化存储在项目根目录 `.api_env` 文件中（已加入 .gitignore）。

## 快速开始

### 前置条件

- macOS
- Python >= 3.11
- Node.js >= 18
- [uv](https://docs.astral.sh/uv/)（Python 包管理）

```bash
# 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 安装 + 构建 + 启动

```bash
# 1. 安装依赖
make install

# 2. 构建前端
make build

# 3. 启动桌面应用
make start
```

或手动执行：

```bash
uv sync                              # 安装 Python 依赖
cd frontend && npm install && npm run build  # 构建前端
cd backend && uv run python -m miniotter     # 启动桌面应用
```

启动后会自动打开桌面窗口，在 Settings 页面配置 LLM API Key 即可使用。

### 启动模式

```bash
# 桌面应用（默认）— 打开原生窗口
cd backend && uv run python -m miniotter

# 仅后端 — 不打开窗口，浏览器访问 http://127.0.0.1:8000
cd backend && uv run python -m miniotter --server

# 开发模式 — 后端 + 前端热更新（分别在两个终端执行）
make dev-backend     # 终端 1
make dev-frontend    # 终端 2
```

### macOS 权限

GUI Agent 需要以下系统权限：

- **辅助功能** — 系统设置 > 隐私与安全性 > 辅助功能
- **屏幕录制** — 系统设置 > 隐私与安全性 > 屏幕录制

## 项目结构

```
MiniOtter/
├── backend/miniotter/
│   ├── __main__.py      # 入口：桌面窗口(pywebview) + 后台服务(FastAPI)
│   ├── agents/          # 4 个 Agent — 每个文件包含 Agent 类 + 工具 + 系统提示词
│   │   ├── base.py      #   BaseAgent + LLM 提供者工厂
│   │   ├── gui_agent.py #   GUI Agent + 鼠标键盘截图a11y 工具
│   │   ├── text_agent.py#   文本 Agent + bash 文件 剪贴板 工具
│   │   ├── main_agent.py#   主 Agent（路由） + RouteToAgent 工具
│   │   └── extension_agent.py
│   ├── react/           # ReAct Loop 引擎
│   │   ├── engine.py    #   ReActLoop + 步骤历史（核心循环）
│   │   └── types.py     #   Thought / Action / Observation / ReActStep / TaskResult
│   ├── tools/base.py    # BaseTool + TaskComplete + TaskFailed
│   ├── llm/             # LLM 提供者抽象（Claude / OpenAI）
│   ├── macos/           # macOS 平台层（截图 / a11y / 输入控制）
│   ├── app/             # FastAPI 服务 + WebSocket + REST API + 静态文件
│   └── static/          # 前端构建产物（构建时自动生成）
├── frontend/src/
│   ├── pages/Chat/      # 对话页面（消息列表 + ReAct 步骤卡片 + 截图标注）
│   ├── pages/Settings/  # 设置页面（文本LLM + 视觉LLM 分开配置）
│   ├── stores/          # Zustand 状态管理
│   └── hooks/           # WebSocket + 自动滚动
├── docs/architecture.md # 完整技术方案
└── pyproject.toml       # uv 项目配置
```

## 添加依赖

```bash
uv add requests           # 运行时依赖（自动写入 pyproject.toml）
uv add --dev pytest-cov   # 开发依赖
uv remove requests        # 移除
```
