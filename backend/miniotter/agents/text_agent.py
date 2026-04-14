"""Text Agent - handles bash commands and file operations."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from ..tools.base import BaseTool, TaskComplete, TaskFailed, ToolParameter
from .base import BaseAgent

_SYSTEM_PROMPT = """\
你是 MiniOtter 的文本操作Agent。你可以执行bash命令、读写文件，完成不需要图形界面的自动化任务。

## 可用工具

### 命令执行
- `execute_bash(command, timeout)`: 执行bash命令。返回 stdout、stderr 和退出码。默认超时30秒。

### 文件操作
- `read_file(path, offset, limit)`: 读取文件内容。offset 和 limit 控制读取范围。
- `write_file(path, content)`: 将内容写入文件（创建或覆盖）。
- `list_directory(path)`: 列出目录中的文件和子目录。

### 剪贴板
- `get_clipboard()`: 获取当前剪贴板中的文本内容。
- `set_clipboard(content)`: 将文本设置到剪贴板。

### 任务控制
- `task_complete(message)`: 任务完成，附上总结。
- `task_failed(reason)`: 任务失败，说明原因。

## 工作原则

1. **安全第一**：执行命令前考虑其影响。避免执行 `rm -rf /`、`sudo` 等危险命令，除非用户明确要求。
2. **分步执行**：复杂任务拆分为多个步骤，每步执行一个命令并检查结果。
3. **错误处理**：如果命令执行失败（返回非零退出码），分析stderr输出，决定是重试、修改命令还是报告失败。
4. **路径安全**：使用绝对路径避免歧义。在操作文件前确认路径存在。
5. **输出处理**：如果命令输出很长，只关注关键信息。必要时使用 head/tail/grep 过滤输出。

## 注意事项

- 所有命令在 macOS 环境下执行
- 使用 macOS 兼容的命令（如 `open` 而非 `xdg-open`）
- 当前工作目录为用户主目录
- 所有回复使用中文
"""


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


class ReadFile(BaseTool):
    name = "read_file"
    description = "读取指定路径文件的内容。对于大文件，可以使用offset和limit参数分段读取。"
    parameters = [
        ToolParameter(name="path", type="string", description="文件的绝对路径"),
        ToolParameter(name="offset", type="integer", description="从第几行开始读取（0-based），默认0", required=False, default=0),
        ToolParameter(name="limit", type="integer", description="最多读取多少行，默认500", required=False, default=500),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        path = kwargs["path"]
        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", 500)
        try:
            p = Path(path)
            if not p.exists():
                return {"error": f"文件不存在: {path}"}
            if not p.is_file():
                return {"error": f"不是文件: {path}"}
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            total = len(lines)
            selected = lines[offset: offset + limit]
            return {"content": "".join(selected), "total_lines": total, "offset": offset, "lines_read": len(selected)}
        except Exception as e:
            return {"error": str(e)}


class WriteFile(BaseTool):
    name = "write_file"
    description = "将内容写入指定路径的文件。如果文件不存在则创建，存在则覆盖。自动创建所需的父目录。"
    parameters = [
        ToolParameter(name="path", type="string", description="文件的绝对路径"),
        ToolParameter(name="content", type="string", description="要写入的完整文件内容"),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        path = kwargs["path"]
        content = kwargs["content"]
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"ok": True, "path": str(p), "bytes_written": len(content.encode("utf-8"))}
        except Exception as e:
            return {"error": str(e)}


class ListDirectory(BaseTool):
    name = "list_directory"
    description = "列出指定目录中的文件和子目录，包含类型（文件/目录）和大小信息。"
    parameters = [
        ToolParameter(name="path", type="string", description="目录路径，默认为当前工作目录", required=False),
    ]

    async def execute(self, **kwargs: Any) -> dict:
        path = kwargs.get("path", os.getcwd())
        try:
            p = Path(path)
            if not p.exists():
                return {"error": f"目录不存在: {path}"}
            if not p.is_dir():
                return {"error": f"不是目录: {path}"}
            entries = []
            for item in sorted(p.iterdir()):
                entry: dict[str, Any] = {"name": item.name, "type": "directory" if item.is_dir() else "file"}
                if item.is_file():
                    entry["size"] = item.stat().st_size
                entries.append(entry)
            return {"path": str(p), "entries": entries, "count": len(entries)}
        except Exception as e:
            return {"error": str(e)}


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


class TextAgent(BaseAgent):
    agent_type = "text"

    def _register_tools(self) -> list[BaseTool]:
        return [
            ExecuteBash(default_timeout=self.config.text_agent.bash_timeout),
            ReadFile(), WriteFile(), ListDirectory(),
            GetClipboard(), SetClipboard(),
            TaskComplete(), TaskFailed(),
        ]

    def _get_system_prompt(self) -> str:
        return _SYSTEM_PROMPT

    def _get_max_steps(self) -> int:
        return self.config.text_agent.max_steps
