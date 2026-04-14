# MiniOtter -- Complete Technical Architecture Document

## 0. 桌面应用架构

MiniOtter 是一个桌面应用，不需要分别启动前后端。采用 **pywebview + FastAPI** 方案：

- 主进程启动 pywebview 原生窗口（macOS 上使用 WebKit）
- 后台 daemon 线程运行 FastAPI HTTP/WebSocket 服务
- 前端 React 构建后作为静态文件由 FastAPI 提供服务
- 一个命令 `python -m miniotter` 同时启动前后端，打开桌面窗口

```
┌─────────────────────────────────┐
│  pywebview 原生窗口 (WebKit)     │
│  ┌───────────────────────────┐  │
│  │  React SPA (静态文件)      │  │
│  │  http://127.0.0.1:8000    │  │
│  └──────────┬────────────────┘  │
│             │ HTTP/WS           │
│  ┌──────────▼────────────────┐  │
│  │  FastAPI (daemon thread)  │  │
│  │  REST API + WebSocket     │  │
│  │  Agent 引擎               │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

启动模式：
- `python -m miniotter` — 桌面应用（默认）
- `python -m miniotter --server` — 仅后端服务
- `python -m miniotter --dev` — 开发模式（配合 `npm run dev` 热更新）

## 1. Project Directory Structure

```
MiniOtter/
├── LICENSE
├── README.md
├── pyproject.toml                     # Python project metadata (backend)
├── Makefile                           # Dev convenience commands
├── .env.example                       # Environment variable template
│
├── backend/                           # Python backend
│   ├── miniotter/
│   │   ├── __init__.py
│   │   ├── __main__.py                # python -m miniotter entry point
│   │   ├── config.py                  # Global config loading (YAML/env)
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   │
│   │   ├── app/                       # FastAPI application layer
│   │   │   ├── __init__.py
│   │   │   ├── server.py              # FastAPI app factory + WebSocket /ws/stream
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat.py            # POST /api/chat  (new task)
│   │   │   │   ├── tasks.py           # GET /api/tasks, GET /api/tasks/{id}
│   │   │   │   ├── config.py          # GET/PUT /api/config
│   │   │   │   └── health.py          # GET /api/health
│   │   │   ├── schemas.py             # Pydantic request/response models
│   │   │   └── deps.py                # Dependency injection helpers
│   │   │
│   │   ├── agents/                    # Agent implementations
│   │   │   ├── __init__.py            # Each file = agent class + its tools + system prompt
│   │   │   ├── base.py                # BaseAgent + LLM provider factory (_create_llm)
│   │   │   ├── main_agent.py          # MainAgent + RouteToAgent tool + system prompt
│   │   │   ├── gui_agent.py           # GUIAgent + all GUI tools + a11y logic + system prompt
│   │   │   ├── text_agent.py          # TextAgent + all text tools + system prompt
│   │   │   ├── extension_agent.py     # ExtensionAgent + system prompt
│   │   │   └── registry.py            # Agent registry / factory
│   │   │
│   │   ├── react/                     # ReAct loop engine
│   │   │   ├── __init__.py
│   │   │   ├── engine.py              # ReActLoop + _StepHistory (merged loop + history)
│   │   │   └── types.py               # Thought, Action, Observation, ReActStep, TaskResult
│   │   │
│   │   ├── tools/
│   │   │   └── base.py                # BaseTool + ToolParameter + TaskComplete + TaskFailed
│   │   │
│   │   ├── llm/                       # LLM provider abstraction
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # BaseLLMProvider interface
│   │   │   ├── claude_provider.py     # Anthropic Claude
│   │   │   ├── openai_provider.py     # OpenAI / compatible
│   │   │   └── types.py               # LLMMessage, LLMResponse, ToolCall
│   │   │
│   │   └── macos/                     # macOS platform layer
│   │       ├── __init__.py
│   │       ├── screenshot.py          # screencapture wrapper
│   │       └── input_control.py       # pyautogui mouse/keyboard
│   │
│   ├── config/
│   │   └── default_config.yaml        # Default configuration
│   └── tests/
│       ├── __init__.py
│       ├── test_react_loop.py
│       ├── test_agents.py
│       └── test_llm_providers.py
│
├── frontend/                          # React frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.tsx                   # App entry
│       ├── App.tsx                    # Root component + router
│       ├── vite-env.d.ts
│       │
│       ├── api/
│       │   ├── index.ts              # Axios instance
│       │   ├── chat.ts               # Chat API calls
│       │   ├── config.ts             # Config API calls
│       │   └── types.ts              # API type definitions
│       │
│       ├── stores/
│       │   ├── chatStore.ts          # Zustand: messages, sessions
│       │   ├── agentStore.ts         # Zustand: agent state, active agent
│       │   └── configStore.ts        # Zustand: LLM config, settings
│       │
│       ├── hooks/
│       │   ├── useWebSocket.ts       # WebSocket connection hook
│       │   └── useAutoScroll.ts      # Chat auto-scroll hook
│       │
│       ├── pages/
│       │   ├── Chat/
│       │   │   ├── index.tsx         # Main chat page
│       │   │   ├── Chat.module.css
│       │   │   └── components/
│       │   │       ├── MessageList.tsx
│       │   │       ├── MessageBubble.tsx
│       │   │       ├── InputBar.tsx
│       │   │       ├── AgentStepCard.tsx   # Shows think/act/observe
│       │   │       ├── ScreenshotViewer.tsx
│       │   │       └── ActionOverlay.tsx   # Red dot on screenshot
│       │   └── Settings/
│       │       ├── index.tsx
│       │       └── Settings.module.css
│       │
│       ├── components/
│       │   ├── Layout/
│       │   │   ├── AppLayout.tsx
│       │   │   └── Sidebar.tsx
│       │   ├── AgentBadge.tsx         # Shows which agent is active
│       │   ├── StatusIndicator.tsx    # Agent running/idle status
│       │   └── MarkdownRenderer.tsx
│       │
│       └── styles/
│           └── global.css
│
└── docs/
    ├── architecture.md
    └── setup.md
```

---

## 2. Backend Architecture

### 2.1 ReAct Loop Engine (`backend/miniotter/react/`)

The ReAct loop is the core execution engine shared by all agents. Each agent receives its own instance with its own history.

**Core Types** (`react/types.py`):

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

class StepType(Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"

@dataclass
class Thought:
    content: str  # LLM's reasoning text

@dataclass
class Action:
    tool_name: str
    tool_args: dict[str, Any]
    call_id: str  # Unique ID for this tool call

@dataclass
class Observation:
    call_id: str
    result: Any           # Tool return value
    is_error: bool = False
    screenshot: str | None = None  # base64 if relevant

@dataclass
class ReActStep:
    """One complete think-act-observe cycle."""
    thought: Thought | None = None
    actions: list[Action] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)

@dataclass
class TaskResult:
    success: bool
    summary: str
    steps: list[ReActStep]
```

**Core Loop** (`react/engine.py`):

```python
class ReActLoop:
    def __init__(
        self,
        llm: BaseLLMProvider,
        tools: list[BaseTool],
        system_prompt: str,
        max_steps: int = 30,
        on_step: Callable[[ReActStep, str], Awaitable[None]] | None = None
    ):
        self.llm = llm
        self.tool_map = {t.name: t for t in tools}
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.on_step = on_step  # Callback for streaming to frontend
        self.history = StepHistory()

    async def run(self, user_message: str, images: list[str] | None = None) -> TaskResult:
        """Execute the full ReAct loop until completion or max steps."""
        self.history.add_user_message(user_message, images)

        for step_num in range(self.max_steps):
            step = ReActStep()

            # 1. THINK + ACT: Call LLM with history, get thought + tool calls
            response = await self.llm.chat(
                messages=self.history.to_messages(),
                tools=self._get_tool_schemas(),
                system=self.system_prompt
            )

            # Extract thought (text portion of response)
            if response.text:
                step.thought = Thought(content=response.text)

            # Check for termination (no tool calls = agent is done)
            if not response.tool_calls:
                await self._emit_step(step, "complete")
                return TaskResult(
                    success=True,
                    summary=response.text or "",
                    steps=self.history.steps
                )

            # 2. ACT: Parse tool calls
            for tc in response.tool_calls:
                action = Action(
                    tool_name=tc.name,
                    tool_args=tc.arguments,
                    call_id=tc.id
                )
                step.actions.append(action)

            # Emit step with actions (before observation)
            await self._emit_step(step, "acting")

            # 3. OBSERVE: Execute each tool, collect observations
            for action in step.actions:
                observation = await self._execute_tool(action)
                step.observations.append(observation)

            # Add step to history for next LLM call
            self.history.add_step(step)
            await self._emit_step(step, "observed")

            # Check if the agent called task_complete or task_failed
            for obs in step.observations:
                if obs.call_id in self._terminal_calls:
                    return TaskResult(
                        success=not obs.is_error,
                        summary=obs.result.get("message", ""),
                        steps=self.history.steps
                    )

        # Max steps exceeded
        return TaskResult(success=False, summary="达到最大步数限制", steps=self.history.steps)

    async def _execute_tool(self, action: Action) -> Observation:
        tool = self.tool_map.get(action.tool_name)
        if not tool:
            return Observation(
                call_id=action.call_id,
                result={"error": f"未知工具: {action.tool_name}"},
                is_error=True
            )
        try:
            result = await tool.execute(**action.tool_args)
            return Observation(call_id=action.call_id, result=result)
        except Exception as e:
            return Observation(
                call_id=action.call_id,
                result={"error": str(e)},
                is_error=True
            )

    async def _emit_step(self, step: ReActStep, phase: str):
        if self.on_step:
            await self.on_step(step, phase)
```

The key design principle: the `ReActLoop` is a **generic engine**. Each agent type customizes behavior by providing different `system_prompt`, `tools`, and `llm` configurations. The `on_step` callback is how real-time updates stream to the frontend.

### 2.2 Agent Architecture

**Base Agent** (`agents/base.py`):

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """All agents share this interface."""
    
    agent_type: str  # "main", "gui", "text", "extension"
    
    def __init__(self, config: AgentConfig, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.llm = _create_llm(config.llm)
        self.tools = self._register_tools()
        self.react_loop = ReActLoop(
            llm=self.llm,
            tools=self.tools,
            system_prompt=self._get_system_prompt(),
            max_steps=config.max_steps,
            on_step=self._on_step
        )
    
    @abstractmethod
    def _register_tools(self) -> list[BaseTool]: ...
    
    @abstractmethod
    def _get_system_prompt(self) -> str: ...
    
    async def run(self, task: str, context: dict | None = None) -> TaskResult:
        """Execute a task using this agent's ReAct loop."""
        return await self.react_loop.run(task)
    
    async def _on_step(self, step: ReActStep, phase: str):
        """Forward step events to WebSocket via event bus."""
        await self.event_bus.emit("agent_step", {
            "agent_type": self.agent_type,
            "step": step,
            "phase": phase
        })
```

**Main Agent (Router)** (`agents/main_agent.py`):

The Main Agent's **sole job** is task routing. It does NOT execute tasks itself. Its tools are `route_to_gui_agent`, `route_to_text_agent`, and `route_to_extension_agent`. When the Main Agent calls one of these "tools", the backend actually spawns the appropriate sub-agent and runs its ReAct loop.

```python
class MainAgent(BaseAgent):
    agent_type = "main"

    def __init__(self, config, event_bus, agent_registry):
        self.agent_registry = agent_registry
        super().__init__(config, event_bus)

    def _register_tools(self) -> list[BaseTool]:
        return [
            RouteToAgent("route_to_gui", "gui", self.agent_registry, self.event_bus),
            RouteToAgent("route_to_text", "text", self.agent_registry, self.event_bus),
            RouteToAgent("route_to_extension", "extension", self.agent_registry, self.event_bus),
        ]

    def _get_system_prompt(self) -> str:
        return MAIN_AGENT_SYSTEM_PROMPT
```

The `RouteToAgent` tool is a special tool that, when called, instantiates the target agent and runs it:

```python
class RouteToAgent(BaseTool):
    """Pseudo-tool that delegates to a sub-agent."""
    
    name: str
    target_agent_type: str
    
    async def execute(self, task_description: str, context: str = "") -> dict:
        agent = self.agent_registry.create(self.target_agent_type)
        result = await agent.run(task_description, {"context": context})
        return {
            "success": result.success,
            "summary": result.summary,
            "steps_count": len(result.steps)
        }
```

**GUI Agent** (`agents/gui_agent.py`):

The GUI Agent works in a loop where each cycle begins by taking a fresh screenshot and (optionally) reading the a11y tree, then deciding what GUI action to perform.

```python
class GUIAgent(BaseAgent):
    agent_type = "gui"

    def _register_tools(self) -> list[BaseTool]:
        return [
            # Observation tools
            TakeScreenshot(),
            GetAccessibilityTree(),
            # Mouse tools
            MouseClick(),
            MouseDoubleClick(),
            MouseRightClick(),
            MouseDrag(),
            MouseScroll(),
            MouseMove(),
            # Keyboard tools
            TypeText(),
            PressKey(),
            Hotkey(),
            # Termination tools
            TaskComplete(),
            TaskFailed(),
        ]

    def _get_system_prompt(self) -> str:
        return GUI_AGENT_SYSTEM_PROMPT

    async def run(self, task: str, context: dict | None = None) -> TaskResult:
        # GUI agent always starts by taking a screenshot
        initial_screenshot = await take_screenshot_native()
        return await self.react_loop.run(task, images=[initial_screenshot])
```

**Text Agent** (`agents/text_agent.py`):

```python
class TextAgent(BaseAgent):
    agent_type = "text"

    def _register_tools(self) -> list[BaseTool]:
        return [
            ExecuteBash(),
            ReadFile(),
            WriteFile(),
            ListDirectory(),
            GetClipboard(),
            SetClipboard(),
            TaskComplete(),
            TaskFailed(),
        ]

    def _get_system_prompt(self) -> str:
        return TEXT_AGENT_SYSTEM_PROMPT
```

**Agent Registry** (`agents/registry.py`):

```python
class AgentRegistry:
    """Factory for creating agent instances by type."""
    
    _agent_classes: dict[str, type[BaseAgent]] = {
        "main": MainAgent,
        "gui": GUIAgent,
        "text": TextAgent,
        "extension": ExtensionAgent,
    }
    
    def create(self, agent_type: str, **kwargs) -> BaseAgent:
        cls = self._agent_classes[agent_type]
        return cls(config=self.config, event_bus=self.event_bus, **kwargs)
    
    def register(self, agent_type: str, agent_cls: type[BaseAgent]):
        """Register a new agent type for extensibility."""
        self._agent_classes[agent_type] = agent_cls
```

### 2.3 Tool Definitions

**Base Tool** (`tools/base.py`):

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ToolParameter:
    name: str
    type: str           # "string", "integer", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    enum: list[str] | None = None
    default: Any = None

class BaseTool(ABC):
    name: str
    description: str
    parameters: list[ToolParameter]

    def to_schema(self) -> dict:
        """Convert to OpenAI/Anthropic-compatible tool schema."""
        properties = {}
        required = []
        for p in self.parameters:
            properties[p.name] = {"type": p.type, "description": p.description}
            if p.enum:
                properties[p.name]["enum"] = p.enum
            if p.required:
                required.append(p.name)
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    @abstractmethod
    async def execute(self, **kwargs) -> dict: ...
```

**GUI Tools -- Complete Schemas:**

| Tool Name | Parameters | Description |
|-----------|-----------|-------------|
| `take_screenshot` | (none) | Captures current full-screen screenshot, returns base64 PNG |
| `get_accessibility_tree` | `app_name: str (optional)` | Returns the a11y tree of the focused app or specified app as structured text |
| `mouse_click` | `x: int, y: int, button: str = "left"` | Single click at coordinate |
| `mouse_double_click` | `x: int, y: int` | Double click at coordinate |
| `mouse_right_click` | `x: int, y: int` | Right click at coordinate |
| `mouse_drag` | `start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5` | Drag from start to end |
| `mouse_scroll` | `x: int, y: int, direction: str ("up"/"down"), clicks: int = 3` | Scroll at position |
| `mouse_move` | `x: int, y: int` | Move cursor to coordinate |
| `type_text` | `text: str` | Type text string using keyboard |
| `press_key` | `key: str` | Press a single key (e.g., "enter", "tab", "escape", "backspace") |
| `hotkey` | `keys: list[str]` | Press key combination (e.g., ["command", "c"]) |
| `task_complete` | `message: str` | Signal the task is done with summary |
| `task_failed` | `reason: str` | Signal the task has failed |

**Text Tools -- Complete Schemas:**

| Tool Name | Parameters | Description |
|-----------|-----------|-------------|
| `execute_bash` | `command: str, timeout: int = 30` | Execute a bash command, returns stdout+stderr+returncode |
| `read_file` | `path: str, offset: int = 0, limit: int = 500` | Read file contents |
| `write_file` | `path: str, content: str` | Write content to file (create or overwrite) |
| `list_directory` | `path: str = "."` | List files in directory |
| `get_clipboard` | (none) | Get current clipboard text content |
| `set_clipboard` | `content: str` | Set clipboard text content |
| `task_complete` | `message: str` | Signal the task is done |
| `task_failed` | `reason: str` | Signal the task has failed |

### 2.4 LLM Provider Abstraction (`llm/`)

```python
# llm/types.py
@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant", "tool"
    content: str | list[dict]  # text or multimodal blocks
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None

@dataclass 
class ToolCall:
    id: str
    name: str
    arguments: dict

@dataclass
class LLMResponse:
    text: str | None
    tool_calls: list[ToolCall]
    usage: dict  # {"input_tokens": int, "output_tokens": int}
    stop_reason: str  # "end_turn", "tool_use", "max_tokens"

# llm/base.py
class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0
    ) -> LLMResponse: ...

# llm/claude_provider.py
class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def chat(self, messages, tools=None, system=None, **kwargs) -> LLMResponse:
        # Convert internal format to Anthropic API format
        # Handle vision (base64 images in content blocks)
        # Map tool_use / tool_result blocks
        ...

# llm/openai_provider.py
class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    async def chat(self, messages, tools=None, system=None, **kwargs) -> LLMResponse:
        # Convert internal format to OpenAI API format
        # Map function_call / tool_calls
        ...

# agents/base.py -- provider factory inlined here (no separate provider_factory.py)
_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}

def _create_llm(llm_config: LLMConfig) -> BaseLLMProvider:
    provider_cls = _PROVIDERS[llm_config.provider]
    return provider_cls(
        api_key=llm_config.api_key,
        model=llm_config.model,
    )
```

### 2.5 macOS Platform Layer (`macos/`)

**Screenshot** (`macos/screenshot.py`) and **Input Control** (`macos/input_control.py`) are the only two files in the macOS layer. The accessibility tree logic is inlined as private functions inside `agents/gui_agent.py` since it is only used there.

**Screenshot** (`macos/screenshot.py`):

Uses macOS native `screencapture` command for reliability and quality. Falls back to `mss` library for programmatic capture.

```python
import subprocess
import base64
import tempfile
from pathlib import Path

async def take_screenshot_native(region: tuple[int,int,int,int] | None = None) -> str:
    """
    Capture screenshot using macOS native screencapture.
    Returns base64-encoded PNG string.
    """
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name
    
    cmd = ["screencapture", "-x", "-C"]  # -x = no sound, -C = capture cursor
    if region:
        x, y, w, h = region
        cmd.extend(["-R", f"{x},{y},{w},{h}"])
    cmd.append(tmp_path)
    
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.wait()
    
    img_bytes = Path(tmp_path).read_bytes()
    Path(tmp_path).unlink()
    
    # Optionally resize for LLM consumption (like Anthropic recommends XGA)
    img_bytes = _resize_for_llm(img_bytes, max_width=1280, max_height=800)
    
    return base64.b64encode(img_bytes).decode()
```

**Accessibility Tree** (private functions inside `agents/gui_agent.py`):

Uses `pyobjc` to traverse the macOS AXUIElement tree. This logic is inlined directly in `gui_agent.py` as private functions since only the GUI Agent uses it.

```python
# agents/gui_agent.py -- private a11y helpers
import ApplicationServices
from AppKit import NSWorkspace

def _get_accessibility_tree(app_name: str | None = None, max_depth: int = 5) -> str:
    if app_name:
        app = _find_app_by_name(app_name)
    else:
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
    
    if not app:
        return "错误：未找到应用程序"
    
    pid = app.processIdentifier()
    app_ref = ApplicationServices.AXUIElementCreateApplication(pid)
    
    tree_lines = []
    _traverse_element(app_ref, depth=0, max_depth=max_depth, lines=tree_lines)
    return "\n".join(tree_lines)

def _traverse_element(element, depth: int, max_depth: int, lines: list[str]):
    if depth > max_depth:
        return
    
    indent = "  " * depth
    role = _get_ax_attribute(element, "AXRole") or "Unknown"
    title = _get_ax_attribute(element, "AXTitle") or ""
    value = _get_ax_attribute(element, "AXValue") or ""
    position = _get_ax_attribute(element, "AXPosition")
    size = _get_ax_attribute(element, "AXSize")
    
    parts = [f"{indent}[{role}]"]
    if title:
        parts.append(f'"{title}"')
    if value:
        parts.append(f"value={value!r}")
    if position and size:
        px, py = int(position.x), int(position.y)
        sw, sh = int(size.width), int(size.height)
        parts.append(f"pos=({px},{py}) size=({sw},{sh})")
    
    lines.append(" ".join(parts))
    
    children = _get_ax_attribute(element, "AXChildren")
    if children:
        for child in children:
            _traverse_element(child, depth + 1, max_depth, lines)
```

**Input Control** (`macos/input_control.py`):

```python
import pyautogui
import time

# Configure pyautogui for macOS
pyautogui.FAILSAFE = True       # Move mouse to corner to abort
pyautogui.PAUSE = 0.1           # Brief pause between actions

async def mouse_click(x: int, y: int, button: str = "left"):
    pyautogui.click(x, y, button=button)

async def mouse_double_click(x: int, y: int):
    pyautogui.doubleClick(x, y)

async def mouse_right_click(x: int, y: int):
    pyautogui.rightClick(x, y)

async def mouse_drag(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5):
    pyautogui.moveTo(start_x, start_y)
    pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)

async def mouse_scroll(x: int, y: int, direction: str, clicks: int = 3):
    pyautogui.moveTo(x, y)
    scroll_amount = clicks if direction == "up" else -clicks
    pyautogui.scroll(scroll_amount)

async def mouse_move(x: int, y: int):
    pyautogui.moveTo(x, y)

async def type_text(text: str):
    pyautogui.typewrite(text, interval=0.02) if text.isascii() else _type_unicode(text)

async def press_key(key: str):
    pyautogui.press(key)

async def hotkey(keys: list[str]):
    pyautogui.hotkey(*keys)

def _type_unicode(text: str):
    """Use pbcopy + Cmd+V for non-ASCII text (Chinese characters, etc.)."""
    import subprocess
    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
    pyautogui.hotkey("command", "v")
```

Note the `_type_unicode` function: `pyautogui.typewrite` only handles ASCII. For Chinese text input, we copy to clipboard and paste via Cmd+V.

### 2.6 API Design (REST + WebSocket)

**REST Endpoints:**

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| `POST` | `/api/chat` | Submit a new task | `{ "message": str, "session_id": str? }` | `{ "task_id": str, "status": "started" }` |
| `GET` | `/api/tasks` | List all tasks | - | `[{ "task_id", "status", "created_at", "summary" }]` |
| `GET` | `/api/tasks/{id}` | Get task detail | - | Full task with all ReAct steps |
| `GET` | `/api/config` | Get current config | - | Config object |
| `PUT` | `/api/config` | Update config | Config object | `{ "ok": true }` |
| `GET` | `/api/health` | Health check | - | `{ "status": "ok", "version": str }` |
| `POST` | `/api/chat/{task_id}/cancel` | Cancel running task | - | `{ "ok": true }` |

**WebSocket Endpoint:**

`WS /ws/stream?session_id={id}`

Messages are JSON frames flowing server-to-client:

```typescript
// Server -> Client message types
type WSMessage =
  | { type: "task_started";     task_id: string }
  | { type: "agent_activated";  agent_type: "main"|"gui"|"text"|"extension"; task_id: string }
  | { type: "thought";          agent_type: string; content: string; step_num: number }
  | { type: "action";           agent_type: string; tool_name: string; tool_args: object; step_num: number }
  | { type: "observation";      agent_type: string; tool_name: string; result: object; screenshot?: string; step_num: number }
  | { type: "task_complete";    task_id: string; success: boolean; summary: string }
  | { type: "error";            task_id: string; message: string }
```

The `screenshot` field in `observation` is a base64-encoded PNG that the frontend renders inline. The `action` messages for GUI tools include x/y coordinates that the frontend overlays on the screenshot as a red dot.

**Server Implementation** (`app/server.py`):

```python
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load config, init agent registry
    app.state.config = load_config()
    app.state.agent_registry = AgentRegistry(app.state.config)
    app.state.event_bus = EventBus()
    yield
    # Shutdown: cleanup

app = FastAPI(title="MiniOtter", lifespan=lifespan)
app.include_router(chat_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(health_router, prefix="/api")

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id", "default")
    
    # Subscribe to events for this session
    queue = asyncio.Queue()
    app.state.event_bus.subscribe(session_id, queue)
    
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        app.state.event_bus.unsubscribe(session_id, queue)
```

---

## 3. Frontend Architecture

### 3.1 Tech Stack

- **React 18** + **TypeScript**
- **Vite** for build tooling
- **Zustand** for state management (following CoPaw's pattern)
- **Ant Design** for UI components
- **react-markdown** + **remark-gfm** for rendering markdown
- **CSS Modules** for scoped styling
- Native **WebSocket API** wrapped in a custom hook

### 3.2 State Management (Zustand Stores)

**chatStore.ts:**
```typescript
interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  agentType?: "main" | "gui" | "text" | "extension";
  steps?: AgentStep[];    // ReAct steps rendered inline
}

interface AgentStep {
  stepNum: number;
  thought?: string;
  actions: { toolName: string; toolArgs: Record<string, any> }[];
  observations: { toolName: string; result: any; screenshot?: string }[];
  phase: "thinking" | "acting" | "observed" | "complete";
}

interface ChatStore {
  messages: Message[];
  currentTaskId: string | null;
  isRunning: boolean;
  sendMessage: (content: string) => Promise<void>;
  cancelTask: () => Promise<void>;
  addStep: (step: AgentStep, agentType: string) => void;
}
```

**agentStore.ts:**
```typescript
interface AgentStore {
  activeAgent: string | null;    // Which agent is currently running
  agentHistory: { type: string; startedAt: number; endedAt?: number }[];
  setActiveAgent: (type: string | null) => void;
}
```

**configStore.ts:**
```typescript
interface ConfigStore {
  llmProvider: string;
  llmModel: string;
  apiKey: string;
  maxSteps: number;
  loadConfig: () => Promise<void>;
  saveConfig: (config: Partial<ConfigStore>) => Promise<void>;
}
```

### 3.3 Pages and Components

**Chat Page** (`pages/Chat/index.tsx`) -- the main page:

The chat page is the primary interface. It contains:

1. **MessageList** -- Scrollable list of messages. Each message can be a simple text bubble (user input, final result) or a complex **AgentStepCard** showing the ReAct process.

2. **AgentStepCard** -- The most important UI component. For each ReAct step, it renders:
   - A collapsible "Thinking" section showing the LLM's reasoning (the `thought`)
   - An "Action" badge showing which tool was called and its arguments
   - An "Observation" section showing the tool result
   - For GUI actions: a **ScreenshotViewer** with an **ActionOverlay** (red dot at x,y coordinates where the agent clicked)
   - A step status indicator (spinning while in progress, checkmark when done)

3. **InputBar** -- Text input at the bottom, with send button and a cancel button (visible during execution).

4. **ScreenshotViewer** -- Renders base64 screenshots inline. When the GUI agent acts, it shows the screenshot with a red dot/circle at the click coordinates and a label of the action (e.g., "click (450, 320)").

5. **ActionOverlay** -- SVG overlay on ScreenshotViewer that draws:
   - Red circle at click position
   - Arrow for drag operations (start to end)
   - Scroll indicator for scroll actions

**Settings Page** (`pages/Settings/index.tsx`):

A form to configure:
- LLM Provider (dropdown: Claude, OpenAI, custom)
- Model name (text input)
- API Key (password input)
- Base URL (for OpenAI-compatible endpoints)
- Max steps per agent (number)
- Screenshot resize settings

**Layout** (`components/Layout/`):

- **AppLayout** -- Fixed sidebar + main content area
- **Sidebar** -- App logo, navigation (Chat / Settings), session history list

### 3.4 WebSocket Hook

```typescript
// hooks/useWebSocket.ts
function useWebSocket(sessionId: string) {
  const ws = useRef<WebSocket | null>(null);
  const { addStep, setTaskId, setRunning } = useChatStore();
  const { setActiveAgent } = useAgentStore();

  useEffect(() => {
    const socket = new WebSocket(`ws://localhost:8000/ws/stream?session_id=${sessionId}`);
    
    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      
      switch (msg.type) {
        case "task_started":
          setTaskId(msg.task_id);
          setRunning(true);
          break;
        case "agent_activated":
          setActiveAgent(msg.agent_type);
          break;
        case "thought":
          addStep({ stepNum: msg.step_num, thought: msg.content, phase: "thinking" }, msg.agent_type);
          break;
        case "action":
          // Update current step with action info
          break;
        case "observation":
          // Update current step with observation + optional screenshot
          break;
        case "task_complete":
          setRunning(false);
          setActiveAgent(null);
          break;
      }
    };
    
    ws.current = socket;
    return () => socket.close();
  }, [sessionId]);
}
```

### 3.5 Real-Time Display Strategy

The key UX challenge is showing the multi-agent, multi-step execution in real-time. The design:

1. When a user sends a message, a **user bubble** appears.
2. Below it, an **agent execution card** appears, initially showing "MainAgent is analyzing your request..."
3. When Main Agent routes to a sub-agent, a **nested card** appears: "GUI Agent activated" or "Text Agent activated"
4. Inside that card, each ReAct step renders incrementally:
   - Thought text streams in (if the LLM supports streaming, the thought text can appear character by character)
   - Action appears as a tool badge: `[click (450, 320)]`
   - Observation appears below: the screenshot with overlay, or the bash output, etc.
5. When the task completes, a final **result bubble** shows the summary.
6. All steps are collapsible -- by default, only the latest step is expanded.

---

## 4. Data Flow: Complete Request Lifecycle

```
User types "打开Safari并搜索天气" in InputBar
                    |
                    v
Frontend: POST /api/chat { message: "打开Safari并搜索天气", session_id: "abc" }
                    |
                    v
Backend: Creates Task, returns { task_id: "t1" }
Backend: Pushes WS event { type: "task_started", task_id: "t1" }
                    |
                    v
Backend: Instantiates MainAgent, starts its ReAct loop
MainAgent ReAct Step 1:
  THINK: "用户要打开Safari浏览器并搜索天气，这是一个GUI操作任务，需要鼠标键盘操作。"
  ACT:   route_to_gui(task_description="打开Safari浏览器并在搜索栏中搜索'天气'")
  --> WS: { type: "thought", agent_type: "main", content: "分析任务...", step_num: 1 }
  --> WS: { type: "action", agent_type: "main", tool_name: "route_to_gui", step_num: 1 }
  --> WS: { type: "agent_activated", agent_type: "gui" }
                    |
                    v
Backend: Instantiates GUIAgent, starts its ReAct loop
GUIAgent automatically takes initial screenshot
GUIAgent ReAct Step 1:
  THINK: "我看到桌面。需要找到Safari图标。我在Dock栏看到了Safari。"
  ACT:   mouse_click(x=640, y=780)
  --> WS: { type: "thought", agent_type: "gui", content: "...", step_num: 1 }
  --> WS: { type: "action", agent_type: "gui", tool_name: "mouse_click", tool_args: {x:640,y:780}, step_num: 1 }
  OBSERVE: { "ok": true }
  --> WS: { type: "observation", agent_type: "gui", result: ..., step_num: 1 }
                    |
                    v
GUIAgent ReAct Step 2:
  (Takes new screenshot automatically before each LLM call)
  THINK: "Safari已打开。我看到地址栏在顶部。需要点击地址栏并输入搜索内容。"
  ACT:   mouse_click(x=400, y=52)
  OBSERVE: ...
                    |
                    v
GUIAgent ReAct Step 3:
  ACT:   type_text(text="天气")
  OBSERVE: ...
                    |
                    v
GUIAgent ReAct Step 4:
  ACT:   press_key(key="enter")
  OBSERVE: ...
                    |
                    v
GUIAgent ReAct Step 5:
  (Takes screenshot, sees search results)
  THINK: "搜索结果已经显示，任务完成。"
  ACT:   task_complete(message="已成功打开Safari并搜索'天气'，搜索结果已显示。")
  --> WS: { type: "observation", ..., screenshot: "base64...", step_num: 5 }
                    |
                    v
Backend: GUIAgent returns TaskResult to MainAgent's route_to_gui tool
MainAgent receives observation: { success: true, summary: "..." }
MainAgent responds with final text (no more tool calls = loop ends)
  --> WS: { type: "task_complete", task_id: "t1", success: true, summary: "..." }
                    |
                    v
Frontend: Updates UI, shows final result, stops spinner
```

---

## 5. Configuration

**Configuration File** (`config/default_config.yaml`):

```yaml
# MiniOtter 配置文件

server:
  host: "127.0.0.1"
  port: 8000
  cors_origins: ["http://localhost:5173"]

llm:
  # 默认LLM配置 (可被各Agent覆盖)
  default:
    provider: "claude"          # "claude" | "openai"
    model: "claude-sonnet-4-20250514"
    api_key: "${ANTHROPIC_API_KEY}"  # 支持环境变量引用
    max_tokens: 4096
    temperature: 0.0
  
  # 可为特定Agent配置不同模型
  gui_agent:
    provider: "claude"
    model: "claude-sonnet-4-20250514"  # GUI需要视觉能力
  
  text_agent:
    provider: "openai"
    model: "gpt-4o"
    api_key: "${OPENAI_API_KEY}"
    base_url: null              # 自定义端点

agents:
  main:
    max_steps: 10
  gui:
    max_steps: 30
    screenshot_max_width: 1280
    screenshot_max_height: 800
    include_accessibility_tree: true
    a11y_max_depth: 5
  text:
    max_steps: 20
    bash_timeout: 30
    allowed_paths: []           # 空 = 不限制

macos:
  screenshot_method: "native"   # "native" (screencapture) | "mss"
  input_method: "pyautogui"     # "pyautogui" | "quartz"
  failsafe: true                # 鼠标移到角落时中止
```

Configuration is loaded with this priority: default_config.yaml < user config file (`~/.miniotter/config.yaml`) < environment variables.

**`.env.example`:**
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
MINIOTTER_PORT=8000
```

---

## 6. Chinese System Prompts

System prompts are inlined as `_SYSTEM_PROMPT` constants directly inside each agent file — there is no separate `prompts/` directory.

### 6.1 Main Agent System Prompt (`agents/main_agent.py`)

```python
MAIN_AGENT_SYSTEM_PROMPT = """你是 MiniOtter 的主调度Agent。你的唯一职责是分析用户的任务，然后将任务路由到合适的子Agent执行。

## 你可以调度的子Agent

1. **GUI Agent** (`route_to_gui`): 负责所有需要操作图形界面的任务。包括：
   - 点击、拖拽、滚动等鼠标操作
   - 键盘输入、快捷键
   - 打开/关闭应用程序
   - 在应用程序中进行操作（如浏览器搜索、设置修改等）
   - 任何需要"看屏幕"才能完成的任务

2. **文本Agent** (`route_to_text`): 负责所有基于文本/命令行的任务。包括：
   - 执行bash/shell命令
   - 读写文件
   - 文件系统操作（创建目录、移动文件等）
   - 不需要图形界面的自动化任务

3. **扩展Agent** (`route_to_extension`): 用于未来扩展的特殊任务。目前暂不可用。

## 路由规则

- 仔细分析用户意图，判断任务属于哪个类型
- 如果任务涉及GUI操作（点击、浏览器、应用程序界面），路由到 GUI Agent
- 如果任务是纯文本/命令行操作（执行命令、编辑文件），路由到文本Agent
- 如果任务同时涉及多种操作，将其拆分为子任务，依次路由到不同Agent
- 将任务描述清晰地传递给子Agent，包含足够的上下文信息

## 注意事项

- 你自己不要直接执行任何操作，只负责路由
- 将用户的原始意图准确转化为子Agent可理解的任务描述
- 如果子Agent返回失败，分析原因，考虑是否需要重试或换一个Agent
- 所有回复使用中文
"""
```

### 6.2 GUI Agent System Prompt (`agents/gui_agent.py`)

```python
GUI_AGENT_SYSTEM_PROMPT = """你是 MiniOtter 的 GUI 操作Agent。你可以通过截图观察屏幕，并使用鼠标和键盘来操作 macOS 桌面上的应用程序。

## 工作流程

每一步你都应该：
1. **观察**：查看当前屏幕截图和/或无障碍树（accessibility tree），理解当前界面状态
2. **思考**：分析当前状态与目标之间的差距，决定下一步操作
3. **行动**：执行一个具体的GUI操作

## 可用工具

### 观察工具
- `take_screenshot`: 截取当前屏幕，获取最新画面
- `get_accessibility_tree`: 获取当前活跃应用的无障碍树，包含UI元素的角色、标题、位置和大小信息

### 鼠标操作
- `mouse_click(x, y, button)`: 在指定坐标点击（默认左键）
- `mouse_double_click(x, y)`: 双击
- `mouse_right_click(x, y)`: 右键点击
- `mouse_drag(start_x, start_y, end_x, end_y, duration)`: 拖拽
- `mouse_scroll(x, y, direction, clicks)`: 滚动（"up" 或 "down"）
- `mouse_move(x, y)`: 移动鼠标到指定位置

### 键盘操作
- `type_text(text)`: 输入文本（支持中文）
- `press_key(key)`: 按下单个键（如 "enter", "tab", "escape", "backspace", "delete", "space"）
- `hotkey(keys)`: 按下组合键（如 ["command", "c"] 表示 Cmd+C）

### 任务控制
- `task_complete(message)`: 任务完成，附上总结
- `task_failed(reason)`: 任务失败，说明原因

## 操作指南

1. **坐标定位**：截图坐标从左上角 (0,0) 开始。使用截图中可见的UI元素位置来确定坐标。无障碍树中的 pos=(x,y) size=(w,h) 信息可以帮助你精确定位。
2. **点击目标中心**：点击一个按钮或元素时，瞄准其中心位置。
3. **等待加载**：执行操作后，调用 take_screenshot 查看结果，确认操作是否成功。
4. **一步一操作**：每次只执行一个GUI操作，然后观察结果。不要连续执行多个操作。
5. **中文输入**：type_text 支持中文，直接输入即可。
6. **快捷键**：macOS 使用 "command" 而非 "ctrl"。例如复制是 ["command", "c"]。
7. **异常处理**：如果操作没有产生预期效果，重新截图分析，尝试其他方式。

## 注意事项

- 操作前一定先截图确认当前状态
- 不要猜测界面内容，始终基于最新截图做决策
- 如果多次尝试无法完成任务，调用 task_failed 并说明原因
- 所有回复使用中文
"""
```

### 6.3 Text Agent System Prompt (`agents/text_agent.py`)

```python
TEXT_AGENT_SYSTEM_PROMPT = """你是 MiniOtter 的文本操作Agent。你可以执行bash命令、读写文件，完成不需要图形界面的自动化任务。

## 可用工具

### 命令执行
- `execute_bash(command, timeout)`: 执行bash命令。返回 stdout、stderr 和退出码。默认超时30秒。

### 文件操作
- `read_file(path, offset, limit)`: 读取文件内容。offset 和 limit 控制读取范围。
- `write_file(path, content)`: 将内容写入文件（创建或覆盖）。
- `list_directory(path)`: 列出目录中的文件和子目录。

### 剪贴板
- `get_clipboard()`: 获取当前剪贴板中的文本内容。
- `set_clipboard(content)`: 将文本设置到剪贴板。

### 任务控制
- `task_complete(message)`: 任务完成，附上总结。
- `task_failed(reason)`: 任务失败，说明原因。

## 工作原则

1. **安全第一**：执行命令前考虑其影响。避免执行 `rm -rf /`、`sudo` 等危险命令，除非用户明确要求。
2. **分步执行**：复杂任务拆分为多个步骤，每步执行一个命令并检查结果。
3. **错误处理**：如果命令执行失败（返回非零退出码），分析stderr输出，决定是重试、修改命令还是报告失败。
4. **路径安全**：使用绝对路径避免歧义。在操作文件前确认路径存在。
5. **输出处理**：如果命令输出很长，只关注关键信息。必要时使用 head/tail/grep 过滤输出。

## 注意事项

- 所有命令在 macOS 环境下执行
- 使用 macOS 兼容的命令（如 `open` 而非 `xdg-open`）
- 当前工作目录为用户主目录
- 所有回复使用中文
"""
```

### 6.4 Extension Agent System Prompt (`agents/extension_agent.py`)

```python
EXTENSION_AGENT_SYSTEM_PROMPT = """你是 MiniOtter 的扩展Agent。此Agent为未来功能预留。

当前此Agent尚未配置具体功能。如果你被调用，请返回以下信息：

"扩展Agent暂未启用。请联系开发者添加自定义扩展功能。"

调用 task_failed 并说明原因。
"""
```

---

## 7. Detailed Tool Schemas (JSON Schema Format)

These schemas are what get sent to the LLM as tool definitions.

### 7.1 GUI Agent Tools

```json
[
  {
    "name": "take_screenshot",
    "description": "截取当前屏幕的完整截图。返回截图的base64编码PNG图片。每次操作后调用此工具确认操作结果。",
    "input_schema": {
      "type": "object",
      "properties": {},
      "required": []
    }
  },
  {
    "name": "get_accessibility_tree",
    "description": "获取当前活跃应用程序（或指定应用）的无障碍树。返回UI元素的层级结构，包含角色(role)、标题(title)、值(value)、位置(position)和大小(size)信息。用于精确定位UI元素。",
    "input_schema": {
      "type": "object",
      "properties": {
        "app_name": {
          "type": "string",
          "description": "要获取无障碍树的应用名称。留空则获取当前最前方的应用。"
        }
      },
      "required": []
    }
  },
  {
    "name": "mouse_click",
    "description": "在指定屏幕坐标执行鼠标单击。坐标原点(0,0)在屏幕左上角。",
    "input_schema": {
      "type": "object",
      "properties": {
        "x": { "type": "integer", "description": "点击位置的X坐标（像素）" },
        "y": { "type": "integer", "description": "点击位置的Y坐标（像素）" },
        "button": {
          "type": "string",
          "enum": ["left", "right", "middle"],
          "description": "鼠标按键，默认左键"
        }
      },
      "required": ["x", "y"]
    }
  },
  {
    "name": "mouse_double_click",
    "description": "在指定坐标执行鼠标双击。常用于打开文件或选中文字。",
    "input_schema": {
      "type": "object",
      "properties": {
        "x": { "type": "integer", "description": "双击位置的X坐标" },
        "y": { "type": "integer", "description": "双击位置的Y坐标" }
      },
      "required": ["x", "y"]
    }
  },
  {
    "name": "mouse_right_click",
    "description": "在指定坐标执行鼠标右键点击。用于打开上下文菜单。",
    "input_schema": {
      "type": "object",
      "properties": {
        "x": { "type": "integer", "description": "右键点击位置的X坐标" },
        "y": { "type": "integer", "description": "右键点击位置的Y坐标" }
      },
      "required": ["x", "y"]
    }
  },
  {
    "name": "mouse_drag",
    "description": "从起点坐标拖拽到终点坐标。用于拖动文件、调整窗口大小、选择文本等。",
    "input_schema": {
      "type": "object",
      "properties": {
        "start_x": { "type": "integer", "description": "拖拽起点X坐标" },
        "start_y": { "type": "integer", "description": "拖拽起点Y坐标" },
        "end_x": { "type": "integer", "description": "拖拽终点X坐标" },
        "end_y": { "type": "integer", "description": "拖拽终点Y坐标" },
        "duration": { "type": "number", "description": "拖拽持续时间（秒），默认0.5秒" }
      },
      "required": ["start_x", "start_y", "end_x", "end_y"]
    }
  },
  {
    "name": "mouse_scroll",
    "description": "在指定位置滚动鼠标滚轮。用于页面上下滚动。",
    "input_schema": {
      "type": "object",
      "properties": {
        "x": { "type": "integer", "description": "滚动位置的X坐标" },
        "y": { "type": "integer", "description": "滚动位置的Y坐标" },
        "direction": {
          "type": "string",
          "enum": ["up", "down"],
          "description": "滚动方向"
        },
        "clicks": { "type": "integer", "description": "滚动格数，默认3" }
      },
      "required": ["x", "y", "direction"]
    }
  },
  {
    "name": "mouse_move",
    "description": "移动鼠标到指定坐标，不点击。用于触发悬停效果。",
    "input_schema": {
      "type": "object",
      "properties": {
        "x": { "type": "integer", "description": "目标X坐标" },
        "y": { "type": "integer", "description": "目标Y坐标" }
      },
      "required": ["x", "y"]
    }
  },
  {
    "name": "type_text",
    "description": "使用键盘输入文本。支持中文和其他Unicode字符。在输入前请确保焦点在正确的输入框中。",
    "input_schema": {
      "type": "object",
      "properties": {
        "text": { "type": "string", "description": "要输入的文本内容" }
      },
      "required": ["text"]
    }
  },
  {
    "name": "press_key",
    "description": "按下并释放单个键。常用键名：enter, tab, escape, backspace, delete, space, up, down, left, right, f1-f12。",
    "input_schema": {
      "type": "object",
      "properties": {
        "key": { "type": "string", "description": "键名（如 'enter', 'tab', 'escape'）" }
      },
      "required": ["key"]
    }
  },
  {
    "name": "hotkey",
    "description": "同时按下组合键。macOS上使用'command'而非'ctrl'。例如：复制=['command','c']，粘贴=['command','v']，撤销=['command','z']，全选=['command','a']。",
    "input_schema": {
      "type": "object",
      "properties": {
        "keys": {
          "type": "array",
          "items": { "type": "string" },
          "description": "按键列表，按顺序同时按下。如 ['command', 'shift', 's'] 表示 Cmd+Shift+S"
        }
      },
      "required": ["keys"]
    }
  },
  {
    "name": "task_complete",
    "description": "标记当前任务已成功完成。提供任务完成的总结信息。",
    "input_schema": {
      "type": "object",
      "properties": {
        "message": { "type": "string", "description": "任务完成的总结说明" }
      },
      "required": ["message"]
    }
  },
  {
    "name": "task_failed",
    "description": "标记当前任务失败。提供失败原因。",
    "input_schema": {
      "type": "object",
      "properties": {
        "reason": { "type": "string", "description": "任务失败的原因说明" }
      },
      "required": ["reason"]
    }
  }
]
```

### 7.2 Text Agent Tools

```json
[
  {
    "name": "execute_bash",
    "description": "在macOS上执行bash命令。返回stdout、stderr和退出码。注意：命令在非交互式shell中执行，不支持需要用户输入的交互式命令。",
    "input_schema": {
      "type": "object",
      "properties": {
        "command": { "type": "string", "description": "要执行的bash命令" },
        "timeout": { "type": "integer", "description": "命令超时时间（秒），默认30秒" }
      },
      "required": ["command"]
    }
  },
  {
    "name": "read_file",
    "description": "读取指定路径文件的内容。对于大文件，可以使用offset和limit参数分段读取。",
    "input_schema": {
      "type": "object",
      "properties": {
        "path": { "type": "string", "description": "文件的绝对路径" },
        "offset": { "type": "integer", "description": "从第几行开始读取（0-based），默认0" },
        "limit": { "type": "integer", "description": "最多读取多少行，默认500" }
      },
      "required": ["path"]
    }
  },
  {
    "name": "write_file",
    "description": "将内容写入指定路径的文件。如果文件不存在则创建，存在则覆盖。自动创建所需的父目录。",
    "input_schema": {
      "type": "object",
      "properties": {
        "path": { "type": "string", "description": "文件的绝对路径" },
        "content": { "type": "string", "description": "要写入的完整文件内容" }
      },
      "required": ["path", "content"]
    }
  },
  {
    "name": "list_directory",
    "description": "列出指定目录中的文件和子目录，包含类型（文件/目录）和大小信息。",
    "input_schema": {
      "type": "object",
      "properties": {
        "path": { "type": "string", "description": "目录路径，默认为当前工作目录" }
      },
      "required": []
    }
  },
  {
    "name": "get_clipboard",
    "description": "获取macOS剪贴板中的当前文本内容。",
    "input_schema": {
      "type": "object",
      "properties": {},
      "required": []
    }
  },
  {
    "name": "set_clipboard",
    "description": "将指定文本设置到macOS剪贴板中。",
    "input_schema": {
      "type": "object",
      "properties": {
        "content": { "type": "string", "description": "要设置到剪贴板的文本" }
      },
      "required": ["content"]
    }
  },
  {
    "name": "task_complete",
    "description": "标记当前任务已成功完成。提供任务完成的总结信息。",
    "input_schema": {
      "type": "object",
      "properties": {
        "message": { "type": "string", "description": "任务完成的总结说明" }
      },
      "required": ["message"]
    }
  },
  {
    "name": "task_failed",
    "description": "标记当前任务失败。提供失败原因。",
    "input_schema": {
      "type": "object",
      "properties": {
        "reason": { "type": "string", "description": "任务失败的原因说明" }
      },
      "required": ["reason"]
    }
  }
]
```

### 7.3 Main Agent Tools

```json
[
  {
    "name": "route_to_gui",
    "description": "将任务路由到GUI Agent执行。GUI Agent可以通过截图观察屏幕，并使用鼠标和键盘操作macOS桌面应用程序。适用于所有需要图形界面操作的任务。",
    "input_schema": {
      "type": "object",
      "properties": {
        "task_description": {
          "type": "string",
          "description": "详细的任务描述，包含足够的上下文信息让GUI Agent理解和执行任务"
        },
        "context": {
          "type": "string",
          "description": "可选的额外上下文信息，如之前步骤的结果"
        }
      },
      "required": ["task_description"]
    }
  },
  {
    "name": "route_to_text",
    "description": "将任务路由到文本Agent执行。文本Agent可以执行bash命令、读写文件。适用于不需要图形界面的命令行和文件操作任务。",
    "input_schema": {
      "type": "object",
      "properties": {
        "task_description": {
          "type": "string",
          "description": "详细的任务描述"
        },
        "context": {
          "type": "string",
          "description": "可选的额外上下文信息"
        }
      },
      "required": ["task_description"]
    }
  },
  {
    "name": "route_to_extension",
    "description": "将任务路由到扩展Agent执行。目前此Agent暂未启用，仅作为未来功能预留。",
    "input_schema": {
      "type": "object",
      "properties": {
        "task_description": {
          "type": "string",
          "description": "详细的任务描述"
        },
        "context": {
          "type": "string",
          "description": "可选的额外上下文信息"
        }
      },
      "required": ["task_description"]
    }
  }
]
```

---

## 8. Key Architectural Decisions and Rationale

### 8.1 Why Not AgentScope as a Dependency?

CoPaw uses AgentScope as its underlying framework. For MiniOtter, I recommend **not** depending on AgentScope for these reasons:
- MiniOtter's scope is narrower and more focused (macOS GUI automation only)
- A custom ReAct loop is straightforward (~200 lines) and gives full control
- Avoids the weight and complexity of a general-purpose agent framework
- Easier to debug when something goes wrong in the agent loop

### 8.2 WebSocket vs SSE

WebSocket is chosen over SSE because:
- Bidirectional: allows the frontend to send cancel signals
- Multiple message types: cleaner than trying to encode different event types in SSE
- Better library support in React ecosystem
- CoPaw also uses real-time push via a console push store

### 8.3 Screenshot Strategy

GUI Agent automatically takes a fresh screenshot **before each LLM call** rather than relying on the LLM to explicitly call `take_screenshot`. This ensures the LLM always has current visual context. The `take_screenshot` tool remains available for the LLM to call explicitly when it wants to verify an action's result before deciding the next step.

Implementation: in `GUIAgent.run()`, before each ReAct iteration, intercept and inject the latest screenshot into the message history as an image content block.

### 8.4 Coordinate Scaling

macOS Retina displays have 2x pixel density. Screenshots captured at native resolution would have coordinates that don't match pyautogui's coordinate system (which uses logical points, not pixels). The screenshot module must:
1. Capture at native resolution for quality
2. Record the scale factor (typically 2x on Retina)
3. Resize the image for the LLM (to save tokens -- target ~1280x800)
4. When the LLM returns coordinates, map them back: `actual_x = llm_x * (screen_width / image_width)`

### 8.5 Safety Considerations

- **pyautogui.FAILSAFE = True**: Moving mouse to top-left corner aborts all operations
- **Task cancellation**: Frontend can send cancel via WebSocket; backend sets a cancellation flag checked between ReAct steps
- **Max steps limit**: Prevents infinite loops (30 for GUI, 20 for Text)
- **Bash command safety**: Text Agent prompt explicitly warns against dangerous commands; consider adding a command blocklist

### 8.6 Extension Agent Pattern

The Extension Agent is deliberately minimal. To add a new agent type in the future:
1. Create a new agent file in `agents/` extending `BaseAgent`
2. Define its tool classes and system prompt inline in that same file
3. Register it in `AgentRegistry` (`agents/registry.py`)
4. Add a new `route_to_*` tool to Main Agent (`agents/main_agent.py`)

This requires no changes to the ReAct loop, WebSocket protocol, or frontend rendering logic -- everything is designed to be agent-type-agnostic.

---

## 9. Implementation Sequencing

Recommended implementation order:

**Phase 1 -- Core Infrastructure (Backend)**
1. Project skeleton: pyproject.toml, directory structure, config loading
2. LLM provider abstraction (start with Claude only)
3. ReAct loop engine (`react/engine.py`, `react/types.py`)
4. Tool base class (`tools/base.py`)

**Phase 2 -- Text Agent (Simplest Agent)**
5. Text Agent tools (bash, file ops)
6. Text Agent with system prompt
7. FastAPI server with `/api/chat` endpoint (no WebSocket yet, just blocking)
8. Test end-to-end: send task, Text Agent executes, return result

**Phase 3 -- GUI Agent (Core Feature)**
9. macOS screenshot capture
10. macOS accessibility tree
11. macOS input control (mouse/keyboard)
12. GUI Agent tools wrapping the macOS layer
13. GUI Agent with system prompt
14. Test: GUI Agent can click things on screen

**Phase 4 -- Main Agent + Routing**
15. Main Agent with routing tools
16. Agent registry and factory
17. Full routing flow: user -> Main Agent -> sub-agent -> result

**Phase 5 -- Real-Time Communication**
18. EventBus for agent step events
19. WebSocket endpoint
20. Agent step callbacks wired to EventBus

**Phase 6 -- Frontend**
21. Vite + React project setup
22. WebSocket hook
23. Zustand stores
24. Chat page: MessageList, InputBar
25. AgentStepCard with ReAct step rendering
26. ScreenshotViewer + ActionOverlay
27. Settings page

**Phase 7 -- Polish**
28. Configuration management (YAML, env vars, per-agent LLM)
29. Error handling and recovery
30. OpenAI provider support
31. Session management
32. Documentation

---

### Critical Files for Implementation

- `/Users/yangguosheng/Desktop/work_code/MiniOtter/backend/miniotter/react/engine.py` -- The ReAct loop engine (`ReActLoop` + `_StepHistory`) is the central execution mechanism that all four agents depend on; its design determines the entire agent execution model.
- `/Users/yangguosheng/Desktop/work_code/MiniOtter/backend/miniotter/agents/base.py` -- The BaseAgent abstract class establishes the contract between the ReAct loop, tools, LLM providers, and event streaming; every agent type derives from it. Also contains `_create_llm()` factory.
- `/Users/yangguosheng/Desktop/work_code/MiniOtter/backend/miniotter/agents/gui_agent.py` -- Contains the GUI Agent, all GUI tool classes, and the a11y tree extraction logic (inlined as private functions). The a11y tree extraction via pyobjc is the most technically challenging piece and is what differentiates a capable GUI agent from a purely vision-based one.
- `/Users/yangguosheng/Desktop/work_code/MiniOtter/backend/miniotter/app/server.py` -- The FastAPI app factory, which includes the WebSocket endpoint `/ws/stream` inlined directly. Bridges backend agent execution to frontend real-time display via EventBus subscription, serialization of ReAct steps, and session management.
- `/Users/yangguosheng/Desktop/work_code/MiniOtter/frontend/src/pages/Chat/components/AgentStepCard.tsx` -- This is the most complex frontend component, responsible for rendering the multi-layered ReAct process (thought/action/observation with screenshots and coordinate overlays) in real-time as WebSocket events arrive.