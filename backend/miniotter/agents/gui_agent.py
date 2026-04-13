"""GUI Agent - operates macOS desktop via screenshots and mouse/keyboard."""

from __future__ import annotations

from typing import Any

from ..macos.screenshot import take_screenshot_native
from ..prompts.gui_agent import GUI_AGENT_SYSTEM_PROMPT
from ..react.types import TaskResult
from ..tools.base import BaseTool
from ..tools.common.finish import TaskComplete, TaskFailed
from ..tools.gui.accessibility import GetAccessibilityTree
from ..tools.gui.keyboard import Hotkey, PressKey, TypeText
from ..tools.gui.mouse import MouseClick, MouseDoubleClick, MouseDrag, MouseMove, MouseRightClick, MouseScroll
from ..tools.gui.screenshot import TakeScreenshot
from .base import BaseAgent


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
        return GUI_AGENT_SYSTEM_PROMPT

    def _get_max_steps(self) -> int:
        return self.config.gui_agent.max_steps

    async def run(self, task: str, context: dict[str, Any] | None = None) -> TaskResult:
        gui_config = self.config.gui_agent
        initial_screenshot = await take_screenshot_native(
            max_width=gui_config.screenshot_max_width, max_height=gui_config.screenshot_max_height,
        )
        return await self.react_loop.run(task, images=[initial_screenshot])
