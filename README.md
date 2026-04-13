# MiniOtter

A GUI-based automation agent desktop application for macOS. It understands screen content via screenshots, and operates desktop applications using mouse and keyboard to complete user tasks.

One-click launch — built-in frontend and backend, opens a native desktop window directly.

> [中文文档](README_zh.md)

## Architecture

```
User Input
    ↓
┌─────────────┐
│  Main Agent │  Analyzes task, routes to sub-agents
└──────┬──────┘
       ├──────────────────┐
       ↓                  ↓
┌─────────────┐    ┌─────────────┐
│  GUI Agent  │    │  Text Agent │
│ screenshot  │    │  bash/files │
│ mouse+kbd   │    │  clipboard  │
└─────────────┘    └─────────────┘
```

- **Main Agent** — routes tasks only, decides which sub-agent handles the work
- **GUI Agent** — uses screenshots and accessibility tree to execute mouse/keyboard actions (requires multimodal LLM)
- **Text Agent** — runs bash commands, reads/writes files
- **Extension Agent** — reserved for future use

Each agent has an independent ReAct loop.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Desktop window | pywebview (native WebKit window) |
| Frontend | React 18 + TypeScript + Vite + Zustand |
| Backend | Python + FastAPI + WebSocket |
| Agent engine | Custom ReAct Loop |
| LLM | Claude / OpenAI (configurable) |
| macOS platform | screencapture + pyobjc (a11y) + pyautogui (input) |

## LLM Configuration

The project uses two independent LLMs:

| LLM | Purpose | Requirement |
|-----|---------|-------------|
| Text LLM | Main Agent routing + Text Agent | Any text model |
| Vision LLM | GUI Agent — reads screenshots to operate desktop | Must support image input (multimodal) |

API keys are configured via the in-app Settings page and persisted to `.api_env` in the project root (already in `.gitignore`).

## Quick Start

### Prerequisites

- macOS
- Python >= 3.11
- Node.js >= 18
- [uv](https://docs.astral.sh/uv/) (Python package manager)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install + Build + Run

```bash
# 1. Install dependencies
make install

# 2. Build frontend
make build

# 3. Launch desktop app
make start
```

Or manually:

```bash
uv sync                                          # Install Python dependencies
cd frontend && npm install && npm run build      # Build frontend
cd backend && uv run python -m miniotter         # Launch desktop app
```

After launch, a native window opens automatically. Configure your LLM API keys in the Settings page.

### Launch Modes

```bash
# Desktop app (default) — opens native window
cd backend && uv run python -m miniotter

# Server only — no window, access via browser at http://127.0.0.1:8000
cd backend && uv run python -m miniotter --server

# Dev mode — backend + frontend hot reload (run in two terminals)
make dev-backend     # Terminal 1
make dev-frontend    # Terminal 2
```

### macOS Permissions

The GUI Agent requires the following system permissions:

- **Accessibility** — System Settings > Privacy & Security > Accessibility
- **Screen Recording** — System Settings > Privacy & Security > Screen Recording

## Project Structure

```
MiniOtter/
├── backend/miniotter/
│   ├── __main__.py      # Entry: pywebview desktop window + background FastAPI server
│   ├── agents/          # 4 agents (main / gui / text / extension)
│   ├── react/           # ReAct Loop engine
│   ├── tools/           # Tool definitions (gui: mouse/keyboard/screenshot/a11y · text: bash/file/clipboard)
│   ├── llm/             # LLM provider abstraction (Claude / OpenAI)
│   ├── macos/           # macOS platform layer (screenshot / a11y / input / permissions)
│   ├── prompts/         # System prompts (Chinese)
│   └── app/             # FastAPI server + WebSocket + REST API + static files
├── frontend/src/
│   ├── pages/Chat/      # Chat page (message list + ReAct step cards + screenshot annotations)
│   ├── pages/Settings/  # Settings page (Text LLM + Vision LLM configured separately)
│   ├── stores/          # Zustand state management
│   └── hooks/           # WebSocket + auto-scroll
├── docs/architecture.md # Full technical design
└── pyproject.toml       # uv project config
```

## Adding Dependencies

```bash
uv add requests           # Runtime dependency (auto-updates pyproject.toml)
uv add --dev pytest-cov   # Dev dependency
uv remove requests        # Remove
```
