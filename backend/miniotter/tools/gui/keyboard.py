"""Keyboard operation tools."""

from __future__ import annotations

from typing import Any

from ...macos import input_control
from ..base import BaseTool, ToolParameter


class TypeText(BaseTool):
    name = "type_text"
    description = "使用键盘输入文本。支持中文和其他Unicode字符。在输入前请确保焦点在正确的输入框中。"
    parameters = [
        ToolParameter(name="text", type="string", description="要输入的文本内容"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.type_text(kwargs["text"])
        return {"ok": True, "text": kwargs["text"]}


class PressKey(BaseTool):
    name = "press_key"
    description = "按下并释放单个键。常用键名：enter, tab, escape, backspace, delete, space, up, down, left, right, f1-f12。"
    parameters = [
        ToolParameter(name="key", type="string", description="键名（如 'enter', 'tab', 'escape'）"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.press_key(kwargs["key"])
        return {"ok": True, "key": kwargs["key"]}


class Hotkey(BaseTool):
    name = "hotkey"
    description = "同时按下组合键。macOS上使用'command'而非'ctrl'。例如：复制=['command','c']，粘贴=['command','v']，撤销=['command','z']，全选=['command','a']。"
    parameters = [
        ToolParameter(name="keys", type="array", description="按键列表，按顺序同时按下。如 ['command', 'shift', 's'] 表示 Cmd+Shift+S", items={"type": "string"}),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        await input_control.hotkey(kwargs["keys"])
        return {"ok": True, "keys": kwargs["keys"]}
