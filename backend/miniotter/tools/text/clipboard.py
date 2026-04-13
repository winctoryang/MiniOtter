"""Clipboard tools for macOS."""

from __future__ import annotations

import asyncio
from typing import Any

from ..base import BaseTool, ToolParameter


class GetClipboard(BaseTool):
    name = "get_clipboard"
    description = "获取macOS剪贴板中的当前文本内容。"
    parameters = []

    async def execute(self, **kwargs: Any) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec("pbpaste", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            return {"content": stdout.decode("utf-8", errors="replace")}
        except Exception as e:
            return {"error": str(e)}


class SetClipboard(BaseTool):
    name = "set_clipboard"
    description = "将指定文本设置到macOS剪贴板中。"
    parameters = [
        ToolParameter(name="content", type="string", description="要设置到剪贴板的文本"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        content = kwargs["content"]
        try:
            proc = await asyncio.create_subprocess_exec("pbcopy", stdin=asyncio.subprocess.PIPE)
            await proc.communicate(input=content.encode("utf-8"))
            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}
