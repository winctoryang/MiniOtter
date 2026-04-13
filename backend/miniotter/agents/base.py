"""Base agent with ReAct loop integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from ..config import AppConfig, LLMConfig
from ..llm.base import BaseLLMProvider
from ..llm.provider_factory import ProviderFactory
from ..react.loop import ReActLoop
from ..react.types import ReActStep, TaskResult
from ..tools.base import BaseTool


class BaseAgent(ABC):
    """Each agent has its own independent ReAct loop."""

    agent_type: str

    def __init__(
        self,
        config: AppConfig,
        on_step: Callable[[str, ReActStep, str, int], Awaitable[None]] | None = None,
    ) -> None:
        self.config = config
        self._on_step = on_step
        self.llm = self._create_llm(config.get_llm_config(self.agent_type))
        self.tools = self._register_tools()
        self.react_loop = ReActLoop(
            llm=self.llm,
            tools=self.tools,
            system_prompt=self._get_system_prompt(),
            max_steps=self._get_max_steps(),
            on_step=self._wrap_on_step(),
        )

    def _create_llm(self, llm_config: LLMConfig) -> BaseLLMProvider:
        return ProviderFactory.create(llm_config)

    def _wrap_on_step(self) -> Callable[[ReActStep, str, int], Awaitable[None]] | None:
        if not self._on_step:
            return None

        async def wrapper(step: ReActStep, phase: str, step_num: int) -> None:
            await self._on_step(self.agent_type, step, phase, step_num)

        return wrapper

    @abstractmethod
    def _register_tools(self) -> list[BaseTool]: ...

    @abstractmethod
    def _get_system_prompt(self) -> str: ...

    @abstractmethod
    def _get_max_steps(self) -> int: ...

    async def run(self, task: str, context: dict[str, Any] | None = None) -> TaskResult:
        return await self.react_loop.run(task)

    def cancel(self) -> None:
        self.react_loop.cancel()
