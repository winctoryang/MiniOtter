"""Dependency injection helpers."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from ..agents.registry import AgentRegistry
from ..config import AppConfig
from .event_bus import EventBus


def get_config(request: Request) -> AppConfig:
    return request.app.state.config


def get_event_bus(request: Request) -> EventBus:
    return request.app.state.event_bus


def get_agent_registry(request: Request) -> AgentRegistry:
    return request.app.state.agent_registry


def get_task_store(request: Request) -> dict[str, Any]:
    return request.app.state.task_store
