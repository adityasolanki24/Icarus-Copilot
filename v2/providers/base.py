"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from v2.core.types import Message, ToolDef


class LLMProvider(ABC):
    """Uniform interface every provider must implement."""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> Message:
        """Return a single assistant message, possibly containing tool calls."""
        ...
