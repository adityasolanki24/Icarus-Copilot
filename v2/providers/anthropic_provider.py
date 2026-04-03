"""Anthropic Claude provider."""

from __future__ import annotations

from typing import Any

from v2.core.types import Message, ToolCall, ToolDef
from v2.providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
    ):
        from anthropic import AsyncAnthropic

        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    # ------------------------------------------------------------------
    # Format converters
    # ------------------------------------------------------------------

    @staticmethod
    def _to_anthropic_messages(messages: list[Message]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == "system":
                continue  # passed separately

            if msg.role == "assistant":
                content: list[dict[str, Any]] = []
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        content.append(
                            {
                                "type": "tool_use",
                                "id": tc.id,
                                "name": tc.name,
                                "input": tc.arguments,
                            }
                        )
                result.append({"role": "assistant", "content": content})

            elif msg.role == "tool":
                result.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id or "",
                                "content": msg.content or "",
                            }
                        ],
                    }
                )

            else:
                result.append({"role": msg.role, "content": msg.content or ""})

        return result

    @staticmethod
    def _to_anthropic_tools(tools: list[ToolDef]) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
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
        system_msg = next(
            (m.content for m in messages if m.role == "system"), None
        )

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": self._to_anthropic_messages(messages),
            "max_tokens": 4096,
        }
        if system_msg:
            kwargs["system"] = system_msg
        if tools:
            kwargs["tools"] = self._to_anthropic_tools(tools)

        response = await self.client.messages.create(**kwargs)

        content_text = ""
        tool_calls: list[ToolCall] = []

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        return Message(
            role="assistant",
            content=content_text or None,
            tool_calls=tool_calls or None,
        )
