"""Lightweight pipeline orchestration: sequential and parallel steps."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PipelineContext:
    """Shared mutable state that flows through every pipeline step."""

    def __init__(self, user_request: str = ""):
        self.user_request = user_request
        self._data: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __repr__(self) -> str:
        return f"PipelineContext(keys={list(self._data.keys())})"


class PipelineStep(ABC):
    """Base class for every step in a pipeline."""

    name: str = "step"

    @abstractmethod
    async def execute(self, ctx: PipelineContext) -> None: ...


class FunctionStep(PipelineStep):
    """Runs a plain Python function (sync or async) as a pipeline step."""

    def __init__(self, name: str, fn: Callable, output_key: str | None = None):
        self.name = name
        self._fn = fn
        self._output_key = output_key

    async def execute(self, ctx: PipelineContext) -> None:
        result = self._fn(ctx)
        if asyncio.iscoroutine(result):
            result = await result
        if self._output_key and result is not None:
            ctx.set(self._output_key, result)


class ParallelStep(PipelineStep):
    """Runs several sub-steps concurrently."""

    def __init__(self, name: str, steps: list[PipelineStep]):
        self.name = name
        self.steps = steps

    async def execute(self, ctx: PipelineContext) -> None:
        await asyncio.gather(*(s.execute(ctx) for s in self.steps))


class Pipeline:
    """Executes an ordered list of steps, passing a shared context."""

    def __init__(self, name: str, steps: list[PipelineStep]):
        self.name = name
        self.steps = steps

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        logger.info("Pipeline '%s' starting (%d steps)", self.name, len(self.steps))
        for step in self.steps:
            logger.info("  -> %s", step.name)
            print(f"  [{step.name}] running...")
            await step.execute(ctx)
            print(f"  [{step.name}] done")
        logger.info("Pipeline '%s' complete", self.name)
        return ctx
