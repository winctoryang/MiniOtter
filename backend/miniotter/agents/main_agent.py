"""Main Agent - task router that delegates to sub-agents."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from ..config import AppConfig
from ..prompts.main_agent import MAIN_AGENT_SYSTEM_PROMPT
from ..react.types import ReActStep
from ..tools.base import BaseTool, ToolParameter
from .base import BaseAgent

if TYPE_CHECKING:
    from .registry import AgentRegistry


class RouteToAgent(BaseTool):
    """Pseudo-tool that delegates execution to a sub-agent."""

    def __init__(self, name: str, description: str, target_agent_type: str, agent_registry: AgentRegistry) -> None:
        self.name = name
        self.description = description
        self._target_type = target_agent_type
        self._registry = agent_registry
        self.parameters = [
            ToolParameter(name="task_description", type="string", description="详细的任务描述，包含足够的上下文信息让子Agent理解和执行任务"),
            ToolParameter(name="context", type="string", description="可选的额外上下文信息，如之前步骤的结果", required=False),
        ]

    async def execute(self, **kwargs: Any) -> dict:
        task_description = kwargs["task_description"]
        context = kwargs.get("context", "")
        agent = self._registry.create(self._target_type)
        result = await agent.run(task_description, {"context": context})
        return {"success": result.success, "summary": result.summary, "steps_count": len(result.steps)}


class MainAgent(BaseAgent):
    agent_type = "main"

    def __init__(
        self,
        config: AppConfig,
        on_step: Callable[[str, ReActStep, str, int], Awaitable[None]] | None = None,
        agent_registry: AgentRegistry | None = None,
    ) -> None:
        self._agent_registry = agent_registry
        super().__init__(config, on_step)

    def _register_tools(self) -> list[BaseTool]:
        if not self._agent_registry:
            return []
        return [
            RouteToAgent(name="route_to_gui", description="将任务路由到GUI Agent执行。GUI Agent可以通过截图观察屏幕，并使用鼠标和键盘操作macOS桌面应用程序。适用于所有需要图形界面操作的任务。", target_agent_type="gui", agent_registry=self._agent_registry),
            RouteToAgent(name="route_to_text", description="将任务路由到文本Agent执行。文本Agent可以执行bash命令、读写文件。适用于不需要图形界面的命令行和文件操作任务。", target_agent_type="text", agent_registry=self._agent_registry),
            RouteToAgent(name="route_to_extension", description="将任务路由到扩展Agent执行。目前此Agent暂未启用，仅作为未来功能预留。", target_agent_type="extension", agent_registry=self._agent_registry),
        ]

    def _get_system_prompt(self) -> str:
        return MAIN_AGENT_SYSTEM_PROMPT

    def _get_max_steps(self) -> int:
        return self.config.main_agent.max_steps
