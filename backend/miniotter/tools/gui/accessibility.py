"""Accessibility tree tool."""

from __future__ import annotations

from typing import Any

from ...macos.accessibility import get_accessibility_tree
from ..base import BaseTool, ToolParameter


class GetAccessibilityTree(BaseTool):
    name = "get_accessibility_tree"
    description = "获取当前活跃应用程序（或指定应用）的无障碍树。返回UI元素的层级结构，包含角色(role)、标题(title)、值(value)、位置(position)和大小(size)信息。用于精确定位UI元素。"
    parameters = [
        ToolParameter(name="app_name", type="string", description="要获取无障碍树的应用名称。留空则获取当前最前方的应用。", required=False),
    ]

    def __init__(self, max_depth: int = 5) -> None:
        self._max_depth = max_depth

    async def execute(self, **kwargs: Any) -> dict:
        app_name = kwargs.get("app_name")
        tree_text = get_accessibility_tree(app_name=app_name, max_depth=self._max_depth)
        return {"tree": tree_text}
