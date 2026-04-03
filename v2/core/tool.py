"""Tool definition with automatic JSON-Schema extraction from type hints."""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from typing import Any, Callable, get_type_hints

from v2.core.types import ToolDef

_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _parse_docstring_args(docstring: str) -> dict[str, str]:
    """Extract per-parameter descriptions from a Google-style docstring."""
    descriptions: dict[str, str] = {}
    if not docstring:
        return descriptions

    in_args = False
    current_param: str | None = None

    for line in docstring.split("\n"):
        stripped = line.strip()

        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if stripped.lower().startswith(("returns:", "raises:", "example", "note")):
            in_args = False
            continue

        if in_args and stripped:
            match = re.match(r"(\w+)\s*(?:\(.*?\))?\s*:\s*(.*)", stripped)
            if match:
                current_param = match.group(1)
                descriptions[current_param] = match.group(2).strip()
            elif current_param and stripped:
                descriptions[current_param] += " " + stripped

    return descriptions


class Tool:
    """Wraps a Python callable as an LLM-invocable tool."""

    def __init__(
        self,
        fn: Callable,
        name: str | None = None,
        description: str | None = None,
    ):
        self.fn = fn
        self.name = name or fn.__name__
        raw_doc = fn.__doc__ or ""
        self.description = description or raw_doc.split("\n")[0].strip() or self.name
        self._param_descriptions = _parse_docstring_args(raw_doc)
        self.parameters = self._build_schema()

    def _build_schema(self) -> dict[str, Any]:
        hints = get_type_hints(self.fn)
        sig = inspect.signature(self.fn)

        properties: dict[str, Any] = {}
        required: list[str] = []

        for pname, param in sig.parameters.items():
            if pname in ("self", "cls"):
                continue

            ptype = hints.get(pname, str)
            json_type = _TYPE_MAP.get(ptype, "string")

            prop: dict[str, Any] = {"type": json_type}
            if pname in self._param_descriptions:
                prop["description"] = self._param_descriptions[pname]
            if param.default is not inspect.Parameter.empty:
                prop["default"] = param.default
            else:
                required.append(pname)

            properties[pname] = prop

        schema: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    async def execute(self, **kwargs: Any) -> str:
        result = self.fn(**kwargs)
        if asyncio.iscoroutine(result) or asyncio.isfuture(result):
            result = await result
        if not isinstance(result, str):
            result = json.dumps(result)
        return result

    def to_def(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )


def tool(
    fn: Callable | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Tool | Callable[..., Tool]:
    """Decorator to create a Tool from a function."""
    if fn is None:
        return lambda f: Tool(f, name=name, description=description)  # type: ignore[return-value]
    return Tool(fn, name=name, description=description)
