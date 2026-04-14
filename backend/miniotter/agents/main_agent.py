"""Main Agent - task router that delegates to sub-agents."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from ..config import AppConfig
from ..react.types import ReActStep
from ..tools.base import BaseTool, ToolParameter
from .base import BaseAgent

if TYPE_CHECKING:
    from .registry import AgentRegistry

_SYSTEM_PROMPT = """\
你是 MiniOtter 的主调度Agent。你的唯一职责是分析用户的任务，然后将任务路由到合适的子Agent执行。

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


class RouteToAgent(BaseTool):
    """Pseudo-tool that delegates execution to a sub-agent."""

    def __init__(self, name: str, description: str, target_agent_type: str, agent_registry: AgentRegistry) -> None:
        self.name = name
        self.description = description
        self._target_type = target_agent_type
        self._registry = agent_registry
        self._active_agent: Any = None  # currently running sub-agent
        self.parameters = [
            ToolParameter(name="task_description", type="string", description="详细的任务描述，包含足够的上下文信息让子Agent理解和执行任务"),
            ToolParameter(name="context", type="string", description="可选的额外上下文信息，如之前步骤的结果", required=False),
        ]

    async def execute(self, **kwargs: Any) -> dict:
        task_description = kwargs["task_description"]
        context = kwargs.get("context", "")
        agent = self._registry.create(self._target_type)
        self._active_agent = agent
        try:
            result = await agent.run(task_description, {"context": context})
        finally:
            self._active_agent = None
        return {"success": result.success, "summary": result.summary, "steps_count": len(result.steps)}

    def cancel_active(self) -> None:
        if self._active_agent is not None:
            self._active_agent.cancel()


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
        return _SYSTEM_PROMPT

    def _get_max_steps(self) -> int:
        return self.config.main_agent.max_steps

    def cancel(self) -> None:
        super().cancel()
        # Also cancel whichever sub-agent is currently running
        for tool in self.tools:
            if isinstance(tool, RouteToAgent):
                tool.cancel_active()
