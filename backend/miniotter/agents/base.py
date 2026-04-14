"""Base agent with ReAct loop integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from ..config import AppConfig, LLMConfig
from ..exceptions import ConfigError
from ..llm.base import BaseLLMProvider
from ..llm.claude_provider import ClaudeProvider
from ..llm.openai_provider import OpenAIProvider
from ..react.engine import ReActLoop
from ..react.types import ReActStep, TaskResult
from ..tools.base import BaseTool

_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}


def _create_llm(llm_config: LLMConfig) -> BaseLLMProvider:
    provider_cls = _PROVIDERS.get(llm_config.provider)
    if not provider_cls:
        raise ConfigError(f"未知的 LLM 提供者: {llm_config.provider}，支持: {', '.join(_PROVIDERS.keys())}")
    kwargs: dict[str, Any] = {"api_key": llm_config.api_key, "model": llm_config.model}
    if llm_config.base_url:
        kwargs["base_url"] = llm_config.base_url
    return provider_cls(**kwargs)


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
        self.llm = _create_llm(config.get_llm_config(self.agent_type))
        self.tools = self._register_tools()
        self.react_loop = ReActLoop(
            llm=self.llm,
            tools=self.tools,
            system_prompt=self._get_system_prompt(),
            max_steps=self._get_max_steps(),
            on_step=self._wrap_on_step(),
        )

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
