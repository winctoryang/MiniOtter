"""Base tool abstraction and task termination tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolParameter:
    name: str
    type: str  # "string", "integer", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    enum: list[str] | None = None
    default: Any = None
    items: dict | None = None  # for array type


class BaseTool(ABC):
    name: str
    description: str
    parameters: list[ToolParameter] = []

    def to_schema(self) -> dict:
        properties: dict[str, Any] = {}
        required: list[str] = []
        for p in self.parameters:
            prop: dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            if p.items:
                prop["items"] = p.items
            properties[p.name] = prop
            if p.required:
                required.append(p.name)
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {"type": "object", "properties": properties, "required": required},
        }

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any: ...


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
