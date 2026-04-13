"""Pydantic request/response models."""

from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    task_id: str
    status: str = "started"


class TaskSummary(BaseModel):
    task_id: str
    status: str
    success: bool | None = None
    summary: str = ""
    steps_count: int = 0
    created_at: str = ""


class LLMConfigUpdate(BaseModel):
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None


class ConfigUpdate(BaseModel):
    text_llm: LLMConfigUpdate | None = None
    vision_llm: LLMConfigUpdate | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
