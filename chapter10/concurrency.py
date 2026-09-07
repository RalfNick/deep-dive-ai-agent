"""Finite, bounded fan-out for independent reads; no model-generated code."""
import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


async def bounded_reads(calls: list[tuple[str, Any]], read: Callable[[Any], Awaitable[Any]],
                        limit: int = 2) -> dict:
    if limit < 1 or len({call_id for call_id, _ in calls}) != len(calls):
        raise ValueError("positive limit and unique call IDs required")
    pending = iter(calls)
    results = {}

    async def worker():
        # Taking the next item contains no await; workers share one event loop.
        for call_id, argument in pending:
            try:
                results[call_id] = {"value": await read(argument)}
            except Exception as error:
                # CancelledError is a BaseException on supported Python versions.
                results[call_id] = {"error": type(error).__name__}

    async with asyncio.TaskGroup() as group:
        for _ in range(min(limit, len(calls))):
            group.create_task(worker())
    return dict(sorted(results.items()))
