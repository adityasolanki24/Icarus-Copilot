"""OpenAI (and OpenAI-compatible) provider."""

from __future__ import annotations

import json
from typing import Any

from v2.core.types import Message, ToolCall, ToolDef
from v2.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        from openai import AsyncOpenAI

        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    # ------------------------------------------------------------------
    # Format converters
    # ------------------------------------------------------------------

    @staticmethod
    def _to_openai_messages(messages: list[Message]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == "tool":
                result.append(
                    {
                        "role": "tool",
                        "content": msg.content or "",
                        "tool_call_id": msg.tool_call_id or "",
                    }
                )
            elif msg.role == "assistant" and msg.tool_calls:
                entry: dict[str, Any] = {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
                result.append(entry)
            else:
                result.append({"role": msg.role, "content": msg.content or ""})
        return result

    @staticmethod
    def _to_openai_tools(tools: list[ToolDef]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    # ------------------------------------------------------------------
    # Main API
    # ------------------------------------------------------------------

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> Message:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": self._to_openai_messages(messages),
        }
        if tools:
            kwargs["tools"] = self._to_openai_tools(tools)

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0].message

        tool_calls = None
        if choice.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
                for tc in choice.tool_calls
            ]

        return Message(
            role="assistant",
            content=choice.content,
            tool_calls=tool_calls,
        )
