"""Task termination tools."""

from __future__ import annotations

from typing import Any

from ..base import BaseTool, ToolParameter


class TaskComplete(BaseTool):
    name = "task_complete"
    description = "标记当前任务已成功完成。提供任务完成的总结信息。"
    parameters = [
        ToolParameter(name="message", type="string", description="任务完成的总结说明"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        return {"message": kwargs.get("message", "任务完成")}


class TaskFailed(BaseTool):
    name = "task_failed"
    description = "标记当前任务失败。提供失败原因。"
    parameters = [
        ToolParameter(name="reason", type="string", description="任务失败的原因说明"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        return {"reason": kwargs.get("reason", "未知原因")}
