"""Agent registry and factory."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from ..config import AppConfig
from ..react.types import ReActStep

if TYPE_CHECKING:
    from .base import BaseAgent


class AgentRegistry:
    def __init__(self, config: AppConfig, on_step: Callable[[str, ReActStep, str, int], Awaitable[None]] | None = None) -> None:
        self.config = config
        self._on_step = on_step
        self._agent_classes: dict[str, type[BaseAgent]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        from .gui_agent import GUIAgent
        from .main_agent import MainAgent
        from .text_agent import TextAgent
        from .extension_agent import ExtensionAgent
        self._agent_classes = {"main": MainAgent, "gui": GUIAgent, "text": TextAgent, "extension": ExtensionAgent}

    def create(self, agent_type: str, **kwargs: Any) -> BaseAgent:
        cls = self._agent_classes.get(agent_type)
        if not cls:
            raise ValueError(f"未知的 Agent 类型: {agent_type}")
        if agent_type == "main":
            return cls(config=self.config, on_step=self._on_step, agent_registry=self, **kwargs)
        return cls(config=self.config, on_step=self._on_step, **kwargs)

    def register(self, agent_type: str, agent_cls: type[BaseAgent]) -> None:
        self._agent_classes[agent_type] = agent_cls
