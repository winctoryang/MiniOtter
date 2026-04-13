"""ReAct loop data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Thought:
    """LLM reasoning text."""
    content: str


@dataclass
class Action:
    """A tool call to execute."""
    tool_name: str
    tool_args: dict[str, Any]
    call_id: str


@dataclass
class Observation:
    """Result of a tool execution."""
    call_id: str
    result: Any
    is_error: bool = False
    screenshot: str | None = None  # base64 PNG if relevant


@dataclass
class ReActStep:
    """One complete think-act-observe cycle."""
    thought: Thought | None = None
    actions: list[Action] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)


@dataclass
class TaskResult:
    """Final result of an agent run."""
    success: bool
    summary: str
    steps: list[ReActStep] = field(default_factory=list)
