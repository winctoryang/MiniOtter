"""Chat route - main entry point for user tasks."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from ...agents.registry import AgentRegistry
from ...react.types import ReActStep
from ..deps import get_agent_registry, get_event_bus, get_task_store
from ..event_bus import EventBus
from ..schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def create_chat(
    request: ChatRequest,
    agent_registry: AgentRegistry = Depends(get_agent_registry),
    event_bus: EventBus = Depends(get_event_bus),
    task_store: dict[str, Any] = Depends(get_task_store),
):
    task_id = str(uuid.uuid4())[:8]
    task_store[task_id] = {
        "task_id": task_id, "status": "running",
        "message": request.message, "created_at": datetime.now(timezone.utc).isoformat(),
    }
    asyncio.create_task(_run_agent(task_id, request.session_id, request.message, agent_registry, event_bus, task_store))
    return ChatResponse(task_id=task_id)


@router.post("/chat/{task_id}/cancel")
async def cancel_task(task_id: str, task_store: dict[str, Any] = Depends(get_task_store)):
    task = task_store.get(task_id)
    if not task:
        return {"error": "任务不存在"}
    agent = task.get("_agent")
    if agent:
        agent.cancel()
    task["status"] = "cancelled"
    return {"ok": True}


async def _run_agent(
    task_id: str, session_id: str, message: str,
    agent_registry: AgentRegistry, event_bus: EventBus, task_store: dict[str, Any],
) -> None:
    async def on_step(agent_type: str, step: ReActStep, phase: str, step_num: int) -> None:
        base = {"task_id": task_id, "agent_type": agent_type, "step_num": step_num, "phase": phase}

        if phase in ("acting", "observed"):
            if step.thought:
                await event_bus.emit(session_id, {**base, "type": "thought", "content": step.thought.content})
            for action in step.actions:
                await event_bus.emit(session_id, {**base, "type": "action", "tool_name": action.tool_name, "tool_args": action.tool_args})
            if phase == "observed":
                for obs in step.observations:
                    evt: dict[str, Any] = {**base, "type": "observation", "result": obs.result if not isinstance(obs.result, bytes) else "(binary)", "is_error": obs.is_error}
                    if obs.screenshot:
                        evt["screenshot"] = obs.screenshot
                    await event_bus.emit(session_id, evt)
        elif phase == "complete" and step.thought:
            await event_bus.emit(session_id, {**base, "type": "thought", "content": step.thought.content})

    await event_bus.emit(session_id, {"type": "task_started", "task_id": task_id})

    try:
        reg = AgentRegistry(config=agent_registry.config, on_step=on_step)
        agent = reg.create("main")
        task_store[task_id]["_agent"] = agent

        await event_bus.emit(session_id, {"type": "agent_activated", "task_id": task_id, "agent_type": "main"})

        result = await agent.run(message)
        task_store[task_id].update({"status": "completed", "success": result.success, "summary": result.summary, "steps_count": len(result.steps)})
        await event_bus.emit(session_id, {"type": "task_complete", "task_id": task_id, "success": result.success, "summary": result.summary})
    except Exception as e:
        logger.exception("Task %s failed", task_id)
        task_store[task_id].update({"status": "failed", "error": str(e)})
        await event_bus.emit(session_id, {"type": "error", "task_id": task_id, "message": str(e)})
