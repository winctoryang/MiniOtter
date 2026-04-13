"""Mouse operation tools."""

from __future__ import annotations

from typing import Any

from ...macos import input_control
from ..base import BaseTool, ToolParameter


class MouseClick(BaseTool):
    name = "mouse_click"
    description = "在指定屏幕坐标执行鼠标单击。坐标原点(0,0)在屏幕左上角。"
    parameters = [
        ToolParameter(name="x", type="integer", description="点击位置的X坐标（像素）"),
        ToolParameter(name="y", type="integer", description="点击位置的Y坐标（像素）"),
        ToolParameter(name="button", type="string", description="鼠标按键，默认左键", required=False, enum=["left", "right", "middle"]),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_click(kwargs["x"], kwargs["y"], kwargs.get("button", "left"))
        return {"ok": True, "x": kwargs["x"], "y": kwargs["y"]}


class MouseDoubleClick(BaseTool):
    name = "mouse_double_click"
    description = "在指定坐标执行鼠标双击。常用于打开文件或选中文字。"
    parameters = [
        ToolParameter(name="x", type="integer", description="双击位置的X坐标"),
        ToolParameter(name="y", type="integer", description="双击位置的Y坐标"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_double_click(kwargs["x"], kwargs["y"])
        return {"ok": True, "x": kwargs["x"], "y": kwargs["y"]}


class MouseRightClick(BaseTool):
    name = "mouse_right_click"
    description = "在指定坐标执行鼠标右键点击。用于打开上下文菜单。"
    parameters = [
        ToolParameter(name="x", type="integer", description="右键点击位置的X坐标"),
        ToolParameter(name="y", type="integer", description="右键点击位置的Y坐标"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_right_click(kwargs["x"], kwargs["y"])
        return {"ok": True, "x": kwargs["x"], "y": kwargs["y"]}


class MouseDrag(BaseTool):
    name = "mouse_drag"
    description = "从起点坐标拖拽到终点坐标。用于拖动文件、调整窗口大小、选择文本等。"
    parameters = [
        ToolParameter(name="start_x", type="integer", description="拖拽起点X坐标"),
        ToolParameter(name="start_y", type="integer", description="拖拽起点Y坐标"),
        ToolParameter(name="end_x", type="integer", description="拖拽终点X坐标"),
        ToolParameter(name="end_y", type="integer", description="拖拽终点Y坐标"),
        ToolParameter(name="duration", type="number", description="拖拽持续时间（秒），默认0.5秒", required=False),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_drag(kwargs["start_x"], kwargs["start_y"], kwargs["end_x"], kwargs["end_y"], kwargs.get("duration", 0.5))
        return {"ok": True}


class MouseScroll(BaseTool):
    name = "mouse_scroll"
    description = "在指定位置滚动鼠标滚轮。用于页面上下滚动。"
    parameters = [
        ToolParameter(name="x", type="integer", description="滚动位置的X坐标"),
        ToolParameter(name="y", type="integer", description="滚动位置的Y坐标"),
        ToolParameter(name="direction", type="string", description="滚动方向", enum=["up", "down"]),
        ToolParameter(name="clicks", type="integer", description="滚动格数，默认3", required=False),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_scroll(kwargs["x"], kwargs["y"], kwargs["direction"], kwargs.get("clicks", 3))
        return {"ok": True}


class MouseMove(BaseTool):
    name = "mouse_move"
    description = "移动鼠标到指定坐标，不点击。用于触发悬停效果。"
    parameters = [
        ToolParameter(name="x", type="integer", description="目标X坐标"),
        ToolParameter(name="y", type="integer", description="目标Y坐标"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.mouse_move(kwargs["x"], kwargs["y"])
        return {"ok": True, "x": kwargs["x"], "y": kwargs["y"]}
