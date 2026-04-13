"""Screenshot tool."""

from __future__ import annotations

from typing import Any

from ...macos.screenshot import take_screenshot_native
from ..base import BaseTool


class TakeScreenshot(BaseTool):
    name = "take_screenshot"
    description = "截取当前屏幕的完整截图。返回截图的base64编码PNG图片。每次操作后调用此工具确认操作结果。"
    parameters = []

    def __init__(self, max_width: int = 1280, max_height: int = 800) -> None:
        self._max_width = max_width
        self._max_height = max_height

    async def execute(self, **kwargs: Any) -> dict:
        img_b64 = await take_screenshot_native(max_width=self._max_width, max_height=self._max_height)
        return {"screenshot": img_b64, "ok": True}
