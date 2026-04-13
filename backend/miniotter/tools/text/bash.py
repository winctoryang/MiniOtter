"""Bash command execution tool."""

from __future__ import annotations

import asyncio
from typing import Any

from ..base import BaseTool, ToolParameter


class ExecuteBash(BaseTool):
    name = "execute_bash"
    description = "在macOS上执行bash命令。返回stdout、stderr和退出码。注意：命令在非交互式shell中执行，不支持需要用户输入的交互式命令。"
    parameters = [
        ToolParameter(name="command", type="string", description="要执行的bash命令"),
        ToolParameter(name="timeout", type="integer", description="命令超时时间（秒），默认30秒", required=False, default=30),
    ]

    def __init__(self, default_timeout: int = 30) -> None:
        self._default_timeout = default_timeout

    async def execute(self, **kwargs: Any) -> dict:
        command = kwargs["command"]
        timeout = kwargs.get("timeout", self._default_timeout)
        try:
            proc = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")
            max_len = 10000
            if len(stdout_text) > max_len:
                stdout_text = stdout_text[:max_len] + f"\n... (截断，共 {len(stdout.decode())} 字符)"
            if len(stderr_text) > max_len:
                stderr_text = stderr_text[:max_len] + f"\n... (截断，共 {len(stderr.decode())} 字符)"
            return {"stdout": stdout_text, "stderr": stderr_text, "returncode": proc.returncode}
        except asyncio.TimeoutError:
            return {"stdout": "", "stderr": f"命令执行超时（{timeout}秒）", "returncode": -1}
