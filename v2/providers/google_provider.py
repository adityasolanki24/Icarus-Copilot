"""Google Gemini provider via the google-genai SDK."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import uuid4

from v2.core.types import Message, ToolCall, ToolDef
from v2.providers.base import LLMProvider


class GoogleProvider(LLMProvider):
    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None):
        from google import genai

        self.model = model
        self.client = genai.Client(api_key=api_key)

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> Message:
        from google.genai import types

        contents: list[Any] = []
        system_instruction: str | None = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content

            elif msg.role == "user":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=msg.content or "")],
                    )
                )

            elif msg.role == "assistant":
                parts: list[Any] = []
                if msg.content:
                    parts.append(types.Part.from_text(text=msg.content))
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append(
                            types.Part.from_function_call(
                                name=tc.name, args=tc.arguments
                            )
                        )
                if parts:
                    contents.append(types.Content(role="model", parts=parts))

            elif msg.role == "tool":
                fn_response = types.Part.from_function_response(
                    name=msg.name or "",
                    response={"result": msg.content or ""},
                )
                contents.append(types.Content(parts=[fn_response]))

        google_tools = None
        if tools:
            declarations = [
                types.FunctionDeclaration(
                    name=t.name,
                    description=t.description,
                    parameters=_adapt_schema(t.parameters),
                )
                for t in tools
            ]
            google_tools = [types.Tool(function_declarations=declarations)]

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=google_tools,
        )

        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=contents,
            config=config,
        )

        content_text = ""
        tool_calls: list[ToolCall] = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    content_text += part.text
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_calls.append(
                        ToolCall(
                            id=f"call_{uuid4().hex[:12]}",
                            name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        )
                    )

        return Message(
            role="assistant",
            content=content_text or None,
            tool_calls=tool_calls or None,
        )


def _adapt_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Strip JSON-Schema keys that Gemini's FunctionDeclaration rejects."""
    cleaned: dict[str, Any] = {}
    for k, v in schema.items():
        if k == "default":
            continue
        if isinstance(v, dict):
            cleaned[k] = _adapt_schema(v)
        else:
            cleaned[k] = v
    return cleaned
