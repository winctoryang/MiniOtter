"""Extension Agent - reserved for future extensibility."""

from __future__ import annotations

from ..prompts.extension_agent import EXTENSION_AGENT_SYSTEM_PROMPT
from ..tools.base import BaseTool
from ..tools.common.finish import TaskComplete, TaskFailed
from .base import BaseAgent


class ExtensionAgent(BaseAgent):
    agent_type = "extension"

    def _register_tools(self) -> list[BaseTool]:
        return [TaskComplete(), TaskFailed()]

    def _get_system_prompt(self) -> str:
        return EXTENSION_AGENT_SYSTEM_PROMPT

    def _get_max_steps(self) -> int:
        return 5
