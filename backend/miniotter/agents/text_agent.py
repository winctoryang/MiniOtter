"""Text Agent - handles bash commands and file operations."""

from __future__ import annotations

from ..prompts.text_agent import TEXT_AGENT_SYSTEM_PROMPT
from ..tools.base import BaseTool
from ..tools.common.finish import TaskComplete, TaskFailed
from ..tools.text.bash import ExecuteBash
from ..tools.text.clipboard import GetClipboard, SetClipboard
from ..tools.text.file_ops import ListDirectory, ReadFile, WriteFile
from .base import BaseAgent


class TextAgent(BaseAgent):
    agent_type = "text"

    def _register_tools(self) -> list[BaseTool]:
        return [
            ExecuteBash(default_timeout=self.config.text_agent.bash_timeout),
            ReadFile(), WriteFile(), ListDirectory(),
            GetClipboard(), SetClipboard(),
            TaskComplete(), TaskFailed(),
        ]

    def _get_system_prompt(self) -> str:
        return TEXT_AGENT_SYSTEM_PROMPT

    def _get_max_steps(self) -> int:
        return self.config.text_agent.max_steps
