"""Tiny async resilience decorators (retry with backoff) for outbound adapters."""
from __future__ import annotations

import asyncio
import functools
import random
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def retry(
    attempts: int = 3,
    backoff_seconds: float = 0.1,
    on: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Retry an async call on `on` errors with jittered linear backoff; re-raise the last one."""

    def decorate(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for attempt in range(1, attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except on:
                    if attempt == attempts:
                        raise
                    await asyncio.sleep(backoff_seconds * attempt * random.uniform(0.5, 1.5))
            raise AssertionError("unreachable")

        return wrapper

    return decorate
