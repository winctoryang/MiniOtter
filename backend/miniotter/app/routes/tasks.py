"""Task listing routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..deps import get_task_store

router = APIRouter()


@router.get("/tasks")
async def list_tasks(task_store: dict[str, Any] = Depends(get_task_store)):
    return [
        {
            "task_id": tid,
            "status": t.get("status", "unknown"),
            "success": t.get("success"),
            "summary": t.get("summary", ""),
            "steps_count": t.get("steps_count", 0),
            "created_at": t.get("created_at", ""),
        }
        for tid, t in task_store.items()
    ]


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, task_store: dict[str, Any] = Depends(get_task_store)):
    task = task_store.get(task_id)
    if not task:
        return {"error": "任务不存在"}
    return task
