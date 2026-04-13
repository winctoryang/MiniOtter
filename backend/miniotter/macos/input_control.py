"""macOS mouse and keyboard input control via pyautogui."""

from __future__ import annotations

import asyncio

import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


async def mouse_click(x: int, y: int, button: str = "left") -> None:
    await asyncio.to_thread(pyautogui.click, x, y, button=button)


async def mouse_double_click(x: int, y: int) -> None:
    await asyncio.to_thread(pyautogui.doubleClick, x, y)


async def mouse_right_click(x: int, y: int) -> None:
    await asyncio.to_thread(pyautogui.rightClick, x, y)


async def mouse_drag(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> None:
    def _drag():
        pyautogui.moveTo(start_x, start_y)
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
    await asyncio.to_thread(_drag)


async def mouse_scroll(x: int, y: int, direction: str, clicks: int = 3) -> None:
    def _scroll():
        pyautogui.moveTo(x, y)
        pyautogui.scroll(clicks if direction == "up" else -clicks)
    await asyncio.to_thread(_scroll)


async def mouse_move(x: int, y: int) -> None:
    await asyncio.to_thread(pyautogui.moveTo, x, y)


async def type_text(text: str) -> None:
    if text.isascii():
        await asyncio.to_thread(pyautogui.typewrite, text, interval=0.02)
    else:
        await _type_unicode(text)


async def press_key(key: str) -> None:
    await asyncio.to_thread(pyautogui.press, key)


async def hotkey(keys: list[str]) -> None:
    await asyncio.to_thread(pyautogui.hotkey, *keys)


async def _type_unicode(text: str) -> None:
    """Use pbcopy + Cmd+V for non-ASCII text input."""
    proc = await asyncio.create_subprocess_exec("pbpaste", stdout=asyncio.subprocess.PIPE)
    old_clipboard, _ = await proc.communicate()

    proc = await asyncio.create_subprocess_exec("pbcopy", stdin=asyncio.subprocess.PIPE)
    await proc.communicate(input=text.encode("utf-8"))

    await asyncio.to_thread(pyautogui.hotkey, "command", "v")
    await asyncio.sleep(0.1)

    proc = await asyncio.create_subprocess_exec("pbcopy", stdin=asyncio.subprocess.PIPE)
    await proc.communicate(input=old_clipboard)
