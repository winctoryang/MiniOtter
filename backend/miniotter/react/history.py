"""Conversation and step history manager for ReAct loop."""

from __future__ import annotations

from typing import Any

from .types import ReActStep


class StepHistory:
    """Manages the message history for a ReAct loop session."""

    def __init__(self) -> None:
        self._messages: list[dict[str, Any]] = []
        self._steps: list[ReActStep] = []

    @property
    def steps(self) -> list[ReActStep]:
        return list(self._steps)

    @property
    def messages(self) -> list[dict[str, Any]]:
        return list(self._messages)

    def add_user_message(self, text: str, images: list[str] | None = None) -> None:
        """Add a user message, optionally with base64 images."""
        if images:
            content: list[dict] = []
            for img in images:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img,
                    },
                })
            content.append({"type": "text", "text": text})
            self._messages.append({"role": "user", "content": content})
        else:
            self._messages.append({"role": "user", "content": text})

    def add_assistant_response(self, response_data: dict[str, Any]) -> None:
        """Add the raw assistant response to history."""
        self._messages.append(response_data)

    def add_tool_results(self, tool_results: list[dict[str, Any]]) -> None:
        """Add tool results as a user message (tool_result blocks)."""
        self._messages.append({"role": "user", "content": tool_results})

    def add_step(self, step: ReActStep) -> None:
        """Record a completed ReAct step."""
        self._steps.append(step)

    def inject_images(self, images: list[str]) -> None:
        """Inject fresh screenshots into the conversation for the next LLM call."""
        content: list[dict] = []
        for img in images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img,
                },
            })
        content.append({"type": "text", "text": "这是当前屏幕截图。请根据截图内容决定下一步操作。"})
        self._messages.append({"role": "user", "content": content})
