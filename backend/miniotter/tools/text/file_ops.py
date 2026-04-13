"""File operation tools."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..base import BaseTool, ToolParameter


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
            selected = lines[offset : offset + limit]
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
