"""Agent with automatic tool-calling loop, plus multi-turn ChatSession."""

from __future__ import annotations

import json
import logging
from typing import Any

from v2.core.types import Message
from v2.core.tool import Tool
from v2.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class Agent:
    """Single-turn agent: one user message in, one final text answer out."""

    def __init__(
        self,
        provider: LLMProvider,
        system_prompt: str,
        tools: list[Tool] | None = None,
        name: str = "agent",
        max_iterations: int = 10,
    ):
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools: dict[str, Tool] = {t.name: t for t in (tools or [])}
        self.name = name
        self.max_iterations = max_iterations

    async def run(self, user_message: str, context: dict[str, Any] | None = None) -> str:
        system_content = self.system_prompt
        if context:
            for key, value in context.items():
                system_content = system_content.replace(f"{{{key}}}", str(value))

        messages = [
            Message(role="system", content=system_content),
            Message(role="user", content=user_message),
        ]

        tool_defs = [t.to_def() for t in self.tools.values()] if self.tools else None

        for _ in range(self.max_iterations):
            response = await self.provider.generate(messages, tool_defs)
            messages.append(response)

            if not response.tool_calls:
                return response.content or ""

            logger.info(
                "[%s] Tool calls: %s",
                self.name,
                [tc.name for tc in response.tool_calls],
            )

            for tc in response.tool_calls:
                result = await self._execute_tool(tc.name, tc.arguments)
                messages.append(
                    Message(
                        role="tool",
                        content=result,
                        tool_call_id=tc.id,
                        name=tc.name,
                    )
                )

        last = next(
            (m for m in reversed(messages) if m.role == "assistant" and m.content),
            None,
        )
        return last.content if last else ""

    async def _execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        tool_obj = self.tools.get(name)
        if not tool_obj:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            return await tool_obj.execute(**arguments)
        except Exception as e:
            logger.error("[%s] Tool %s failed: %s", self.name, name, e)
            return json.dumps({"error": str(e)})


class ChatSession:
    """Multi-turn wrapper: keeps conversation history across send() calls."""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.history: list[Message] = []

    async def send(self, user_message: str) -> str:
        self.history.append(Message(role="user", content=user_message))

        messages = [
            Message(role="system", content=self.agent.system_prompt),
            *self.history,
        ]

        tool_defs = (
            [t.to_def() for t in self.agent.tools.values()]
            if self.agent.tools
            else None
        )

        for _ in range(self.agent.max_iterations):
            response = await self.agent.provider.generate(messages, tool_defs)
            messages.append(response)
            self.history.append(response)

            if not response.tool_calls:
                return response.content or ""

            for tc in response.tool_calls:
                result = await self.agent._execute_tool(tc.name, tc.arguments)
                tool_msg = Message(
                    role="tool",
                    content=result,
                    tool_call_id=tc.id,
                    name=tc.name,
                )
                messages.append(tool_msg)
                self.history.append(tool_msg)

        return ""
