"""ReAct loop engine — history manager and reasoning loop."""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from ..exceptions import TaskCancelledError
from ..llm.base import BaseLLMProvider
from ..tools.base import BaseTool
from .types import Action, Observation, ReActStep, TaskResult, Thought

logger = logging.getLogger(__name__)

_TERMINAL_TOOLS = {"task_complete", "task_failed"}


class _StepHistory:
    def __init__(self) -> None:
        self._messages: list[dict[str, Any]] = []
        self._steps: list[ReActStep] = []

    @property
    def steps(self) -> list[ReActStep]:
        return list(self._steps)

    @property
    def messages(self) -> list[dict[str, Any]]:
        return list(self._messages)

    def add_user_message(self, text: str, images: list[str] | None = None) -> None:
        if images:
            content: list[dict] = []
            for img in images:
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": img},
                })
            content.append({"type": "text", "text": text})
            self._messages.append({"role": "user", "content": content})
        else:
            self._messages.append({"role": "user", "content": text})

    def add_assistant_response(self, response_data: dict[str, Any]) -> None:
        self._messages.append(response_data)

    def add_tool_results(self, tool_results: list[dict[str, Any]]) -> None:
        self._messages.append({"role": "user", "content": tool_results})

    def add_step(self, step: ReActStep) -> None:
        self._steps.append(step)

    def inject_images(self, images: list[str]) -> None:
        content: list[dict] = []
        for img in images:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": img},
            })
        content.append({"type": "text", "text": "这是当前屏幕截图。请根据截图内容决定下一步操作。"})
        self._messages.append({"role": "user", "content": content})


class ReActLoop:
    """Generic ReAct (Reasoning + Acting) loop engine.

    Each agent creates its own instance with different system_prompt, tools, and llm.
    The on_step callback streams real-time updates to the frontend.
    """

    def __init__(
        self,
        llm: BaseLLMProvider,
        tools: list[BaseTool],
        system_prompt: str,
        max_steps: int = 30,
        on_step: Callable[[ReActStep, str, int], Awaitable[None]] | None = None,
    ) -> None:
        self.llm = llm
        self.tool_map = {t.name: t for t in tools}
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.on_step = on_step
        self.history = _StepHistory()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    async def run(self, user_message: str, images: list[str] | None = None) -> TaskResult:
        self.history.add_user_message(user_message, images)

        for step_num in range(self.max_steps):
            if self._cancelled:
                raise TaskCancelledError("任务已被取消")

            step = ReActStep()

            # 1. THINK + ACT
            response = await self.llm.chat(
                messages=self.history.messages,
                tools=self._get_tool_schemas(),
                system=self.system_prompt,
            )

            self.history.add_assistant_response(response.raw_message)

            if response.text:
                step.thought = Thought(content=response.text)

            # No tool calls = done
            if not response.tool_calls:
                await self._emit_step(step, "complete", step_num)
                return TaskResult(
                    success=True,
                    summary=response.text or "",
                    steps=self.history.steps + [step],
                )

            # 2. ACT
            for tc in response.tool_calls:
                step.actions.append(Action(
                    tool_name=tc.name,
                    tool_args=tc.arguments,
                    call_id=tc.id,
                ))

            await self._emit_step(step, "acting", step_num)

            # 3. OBSERVE
            tool_results: list[dict[str, Any]] = []
            for action in step.actions:
                observation = await self._execute_tool(action)
                step.observations.append(observation)

                result_content: Any
                if isinstance(observation.result, dict):
                    result_content = json.dumps(observation.result, ensure_ascii=False)
                else:
                    result_content = str(observation.result)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": action.call_id,
                    "content": result_content,
                    "is_error": observation.is_error,
                })

            self.history.add_tool_results(tool_results)
            self.history.add_step(step)
            await self._emit_step(step, "observed", step_num)

            # Check terminal tools
            for action, obs in zip(step.actions, step.observations):
                if action.tool_name in _TERMINAL_TOOLS:
                    success = action.tool_name == "task_complete"
                    summary = ""
                    if isinstance(obs.result, dict):
                        summary = obs.result.get("message", obs.result.get("reason", ""))
                    elif isinstance(obs.result, str):
                        summary = obs.result
                    return TaskResult(success=success, summary=summary, steps=self.history.steps)

        return TaskResult(success=False, summary="达到最大步数限制", steps=self.history.steps)

    async def _execute_tool(self, action: Action) -> Observation:
        tool = self.tool_map.get(action.tool_name)
        if not tool:
            return Observation(call_id=action.call_id, result={"error": f"未知工具: {action.tool_name}"}, is_error=True)
        try:
            result = await tool.execute(**action.tool_args)
            screenshot = None
            if isinstance(result, dict) and "screenshot" in result:
                screenshot = result.pop("screenshot")
            return Observation(call_id=action.call_id, result=result, screenshot=screenshot)
        except Exception as e:
            logger.exception("Tool %s execution failed", action.tool_name)
            return Observation(call_id=action.call_id, result={"error": str(e)}, is_error=True)

    async def _emit_step(self, step: ReActStep, phase: str, step_num: int) -> None:
        if self.on_step:
            await self.on_step(step, phase, step_num)

    def _get_tool_schemas(self) -> list[dict]:
        return [tool.to_schema() for tool in self.tool_map.values()]
