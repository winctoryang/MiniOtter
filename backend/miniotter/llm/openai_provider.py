"""OpenAI-compatible LLM provider."""

from __future__ import annotations

import json
import logging
from typing import Any

import openai

from ..exceptions import LLMError
from .base import BaseLLMProvider
from .types import LLMResponse, ToolCall

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None, **kwargs: Any):
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = openai.AsyncOpenAI(**client_kwargs)
        self.model = model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        oai_messages = self._convert_messages(messages, system)
        kwargs: dict[str, Any] = {
            "model": self.model, "max_tokens": max_tokens, "messages": oai_messages,
        }
        if temperature > 0:
            kwargs["temperature"] = temperature
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except openai.APIError as e:
            raise LLMError(f"OpenAI API 错误: {e}") from e

        choice = response.choices[0]
        message = choice.message

        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id, name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                ))

        raw_content: list[dict] = []
        if message.content:
            raw_content.append({"type": "text", "text": message.content})
        for tc in tool_calls:
            raw_content.append({"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.arguments})

        return LLMResponse(
            text=message.content,
            tool_calls=tool_calls,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            stop_reason=choice.finish_reason or "",
            raw_message={"role": "assistant", "content": raw_content},
        )

    def _convert_messages(self, messages: list[dict[str, Any]], system: str | None) -> list[dict[str, Any]]:
        oai_msgs: list[dict[str, Any]] = []
        if system:
            oai_msgs.append({"role": "system", "content": system})

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "assistant":
                if isinstance(content, list):
                    text_parts, tc_list = [], []
                    for block in content:
                        if block.get("type") == "text":
                            text_parts.append(block["text"])
                        elif block.get("type") == "tool_use":
                            tc_list.append({
                                "id": block["id"], "type": "function",
                                "function": {"name": block["name"], "arguments": json.dumps(block["input"], ensure_ascii=False)},
                            })
                    oai_msg: dict[str, Any] = {"role": "assistant"}
                    if text_parts:
                        oai_msg["content"] = "\n".join(text_parts)
                    if tc_list:
                        oai_msg["tool_calls"] = tc_list
                    oai_msgs.append(oai_msg)
                else:
                    oai_msgs.append({"role": "assistant", "content": content})

            elif role == "user":
                if isinstance(content, list):
                    if content and content[0].get("type") == "tool_result":
                        for block in content:
                            oai_msgs.append({"role": "tool", "tool_call_id": block["tool_use_id"], "content": block.get("content", "")})
                    else:
                        oai_content = []
                        for block in content:
                            if block.get("type") == "text":
                                oai_content.append({"type": "text", "text": block["text"]})
                            elif block.get("type") == "image":
                                source = block["source"]
                                oai_content.append({"type": "image_url", "image_url": {"url": f"data:{source['media_type']};base64,{source['data']}"}})
                        oai_msgs.append({"role": "user", "content": oai_content})
                else:
                    oai_msgs.append({"role": "user", "content": content})

        return oai_msgs

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        return [{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""), "parameters": t.get("input_schema", {})}} for t in tools]
