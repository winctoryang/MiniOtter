"""GUI Agent - operates macOS desktop via screenshots and mouse/keyboard."""

from __future__ import annotations

import logging
from typing import Any

from ..macos import input_control
from ..macos.screenshot import take_screenshot_native
from ..react.types import TaskResult
from ..tools.base import BaseTool, TaskComplete, TaskFailed, ToolParameter
from .base import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
你是 MiniOtter 的 GUI 操作Agent。你可以通过截图观察屏幕，并使用鼠标和键盘来操作 macOS 桌面上的应用程序。

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


class TakeScreenshot(BaseTool):
    name = "take_screenshot"
    description = "截取当前屏幕的完整截图。返回截图的base64编码PNG图片。每次操作后调用此工具确认操作结果。"
    parameters = []

    def __init__(self, max_width: int = 1280, max_height: int = 800) -> None:
        self._max_width = max_width
        self._max_height = max_height

    async def execute(self, **kwargs: Any) -> dict:
        img_b64 = await take_screenshot_native(max_width=self._max_width, max_height=self._max_height)
        return {"screenshot": img_b64, "ok": True}


class GetAccessibilityTree(BaseTool):
    name = "get_accessibility_tree"
    description = "获取当前活跃应用程序（或指定应用）的无障碍树。返回UI元素的层级结构，包含角色(role)、标题(title)、值(value)、位置(position)和大小(size)信息。用于精确定位UI元素。"
    parameters = [
        ToolParameter(name="app_name", type="string", description="要获取无障碍树的应用名称。留空则获取当前最前方的应用。", required=False),
    ]

    def __init__(self, max_depth: int = 5) -> None:
        self._max_depth = max_depth

    async def execute(self, **kwargs: Any) -> dict:
        app_name = kwargs.get("app_name")
        tree_text = _get_accessibility_tree(app_name=app_name, max_depth=self._max_depth)
        return {"tree": tree_text}


class MouseClick(BaseTool):
    name = "mouse_click"
    description = "在指定屏幕坐标执行鼠标单击。坐标原点(0,0)在屏幕左上角。"
    parameters = [
        ToolParameter(name="x", type="integer", description="点击位置的X坐标（像素）"),
        ToolParameter(name="y", type="integer", description="点击位置的Y坐标（像素）"),
        ToolParameter(name="button", type="string", description="鼠标按键，默认左键", required=False, enum=["left", "right", "middle"]),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_click(kwargs["x"], kwargs["y"], kwargs.get("button", "left"))
        return {"ok": True, "x": kwargs["x"], "y": kwargs["y"]}


class MouseDoubleClick(BaseTool):
    name = "mouse_double_click"
    description = "在指定坐标执行鼠标双击。常用于打开文件或选中文字。"
    parameters = [
        ToolParameter(name="x", type="integer", description="双击位置的X坐标"),
        ToolParameter(name="y", type="integer", description="双击位置的Y坐标"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_double_click(kwargs["x"], kwargs["y"])
        return {"ok": True, "x": kwargs["x"], "y": kwargs["y"]}


class MouseRightClick(BaseTool):
    name = "mouse_right_click"
    description = "在指定坐标执行鼠标右键点击。用于打开上下文菜单。"
    parameters = [
        ToolParameter(name="x", type="integer", description="右键点击位置的X坐标"),
        ToolParameter(name="y", type="integer", description="右键点击位置的Y坐标"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_right_click(kwargs["x"], kwargs["y"])
        return {"ok": True, "x": kwargs["x"], "y": kwargs["y"]}


class MouseDrag(BaseTool):
    name = "mouse_drag"
    description = "从起点坐标拖拽到终点坐标。用于拖动文件、调整窗口大小、选择文本等。"
    parameters = [
        ToolParameter(name="start_x", type="integer", description="拖拽起点X坐标"),
        ToolParameter(name="start_y", type="integer", description="拖拽起点Y坐标"),
        ToolParameter(name="end_x", type="integer", description="拖拽终点X坐标"),
        ToolParameter(name="end_y", type="integer", description="拖拽终点Y坐标"),
        ToolParameter(name="duration", type="number", description="拖拽持续时间（秒），默认0.5秒", required=False),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_drag(kwargs["start_x"], kwargs["start_y"], kwargs["end_x"], kwargs["end_y"], kwargs.get("duration", 0.5))
        return {"ok": True}


class MouseScroll(BaseTool):
    name = "mouse_scroll"
    description = "在指定位置滚动鼠标滚轮。用于页面上下滚动。"
    parameters = [
        ToolParameter(name="x", type="integer", description="滚动位置的X坐标"),
        ToolParameter(name="y", type="integer", description="滚动位置的Y坐标"),
        ToolParameter(name="direction", type="string", description="滚动方向", enum=["up", "down"]),
        ToolParameter(name="clicks", type="integer", description="滚动格数，默认3", required=False),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_scroll(kwargs["x"], kwargs["y"], kwargs["direction"], kwargs.get("clicks", 3))
        return {"ok": True}


class MouseMove(BaseTool):
    name = "mouse_move"
    description = "移动鼠标到指定坐标，不点击。用于触发悬停效果。"
    parameters = [
        ToolParameter(name="x", type="integer", description="目标X坐标"),
        ToolParameter(name="y", type="integer", description="目标Y坐标"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_move(kwargs["x"], kwargs["y"])
        return {"ok": True, "x": kwargs["x"], "y": kwargs["y"]}


class TypeText(BaseTool):
    name = "type_text"
    description = "使用键盘输入文本。支持中文和其他Unicode字符。在输入前请确保焦点在正确的输入框中。"
    parameters = [
        ToolParameter(name="text", type="string", description="要输入的文本内容"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.type_text(kwargs["text"])
        return {"ok": True, "text": kwargs["text"]}


class PressKey(BaseTool):
    name = "press_key"
    description = "按下并释放单个键。常用键名：enter, tab, escape, backspace, delete, space, up, down, left, right, f1-f12。"
    parameters = [
        ToolParameter(name="key", type="string", description="键名（如 'enter', 'tab', 'escape'）"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.press_key(kwargs["key"])
        return {"ok": True, "key": kwargs["key"]}


class Hotkey(BaseTool):
    name = "hotkey"
    description = "同时按下组合键。macOS上使用'command'而非'ctrl'。例如：复制=['command','c']，粘贴=['command','v']，撤销=['command','z']，全选=['command','a']。"
    parameters = [
        ToolParameter(name="keys", type="array", description="按键列表，按顺序同时按下。如 ['command', 'shift', 's'] 表示 Cmd+Shift+S", items={"type": "string"}),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.hotkey(kwargs["keys"])
        return {"ok": True, "keys": kwargs["keys"]}


def _get_accessibility_tree(app_name: str | None = None, max_depth: int = 5) -> str:
    try:
        import ApplicationServices
        from AppKit import NSWorkspace
    except ImportError:
        return "错误：pyobjc 未安装，无法获取无障碍树"

    try:
        if app_name:
            app = next(
                (a for a in NSWorkspace.sharedWorkspace().runningApplications()
                 if a.localizedName() and app_name.lower() in a.localizedName().lower()),
                None,
            )
        else:
            app = NSWorkspace.sharedWorkspace().frontmostApplication()

        if not app:
            return "错误：未找到应用程序"

        pid = app.processIdentifier()
        app_ref = ApplicationServices.AXUIElementCreateApplication(pid)
        lines: list[str] = [f"应用: {app.localizedName()} (PID: {pid})"]
        _traverse_element(app_ref, depth=0, max_depth=max_depth, lines=lines)
        return "\n".join(lines)
    except Exception as e:
        logger.exception("Failed to get accessibility tree")
        return f"错误：获取无障碍树失败 - {e}"


def _get_ax_attribute(element: Any, attr_name: str) -> Any:
    import ApplicationServices
    err, value = ApplicationServices.AXUIElementCopyAttributeValue(element, attr_name, None)
    return value if err == 0 else None


def _traverse_element(element: Any, depth: int, max_depth: int, lines: list[str]) -> None:
    if depth > max_depth:
        return
    indent = "  " * depth
    role = _get_ax_attribute(element, "AXRole") or "Unknown"
    title = _get_ax_attribute(element, "AXTitle") or ""
    value = _get_ax_attribute(element, "AXValue") or ""
    description = _get_ax_attribute(element, "AXDescription") or ""
    position = _get_ax_attribute(element, "AXPosition")
    size = _get_ax_attribute(element, "AXSize")

    parts = [f"{indent}[{role}]"]
    if title:
        parts.append(f'"{title}"')
    if value:
        val_str = str(value)
        if len(val_str) > 100:
            val_str = val_str[:100] + "..."
        parts.append(f"value={val_str!r}")
    if description:
        parts.append(f"desc={description!r}")
    if position and size:
        try:
            parts.append(f"pos=({int(position.x)},{int(position.y)}) size=({int(size.width)},{int(size.height)})")
        except (AttributeError, TypeError):
            pass
    lines.append(" ".join(parts))

    children = _get_ax_attribute(element, "AXChildren")
    if children:
        for child in children:
            _traverse_element(child, depth + 1, max_depth, lines)


class GUIAgent(BaseAgent):
    agent_type = "gui"

    def _register_tools(self) -> list[BaseTool]:
        gui_config = self.config.gui_agent
        return [
            TakeScreenshot(max_width=gui_config.screenshot_max_width, max_height=gui_config.screenshot_max_height),
            GetAccessibilityTree(max_depth=gui_config.a11y_max_depth),
            MouseClick(), MouseDoubleClick(), MouseRightClick(),
            MouseDrag(), MouseScroll(), MouseMove(),
            TypeText(), PressKey(), Hotkey(),
            TaskComplete(), TaskFailed(),
        ]

    def _get_system_prompt(self) -> str:
        return _SYSTEM_PROMPT

    def _get_max_steps(self) -> int:
        return self.config.gui_agent.max_steps

    async def run(self, task: str, context: dict[str, Any] | None = None) -> TaskResult:
        gui_config = self.config.gui_agent
        initial_screenshot = await take_screenshot_native(
            max_width=gui_config.screenshot_max_width, max_height=gui_config.screenshot_max_height,
        )
        return await self.react_loop.run(task, images=[initial_screenshot])
