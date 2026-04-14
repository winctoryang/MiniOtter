"""Extension Agent - reserved for future extensibility."""

from __future__ import annotations

from ..tools.base import BaseTool, TaskComplete, TaskFailed
from .base import BaseAgent

_SYSTEM_PROMPT = """\
你是 MiniOtter 的扩展Agent。此Agent为未来功能预留。

当前此Agent尚未配置具体功能。如果你被调用，请返回以下信息：

"扩展Agent暂未启用。请联系开发者添加自定义扩展功能。"

调用 task_failed 并说明原因。
"""


class ExtensionAgent(BaseAgent):
    agent_type = "extension"

    def _register_tools(self) -> list[BaseTool]:
        return [TaskComplete(), TaskFailed()]

    def _get_system_prompt(self) -> str:
        return _SYSTEM_PROMPT

    def _get_max_steps(self) -> int:
        return 5
