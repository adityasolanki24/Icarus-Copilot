"""Shared types for the v2 agent framework."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    """Represents an LLM's request to invoke a tool."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    """Provider-agnostic chat message."""
    role: str                                   # system | user | assistant | tool
    content: str | None = None
    tool_calls: list[ToolCall] | None = None    # set when role == "assistant"
    tool_call_id: str | None = None             # set when role == "tool"
    name: str | None = None                     # tool name when role == "tool"


@dataclass
class ToolDef:
    """JSON-Schema description of a tool, sent to the LLM."""
    name: str
    description: str
    parameters: dict[str, Any]
