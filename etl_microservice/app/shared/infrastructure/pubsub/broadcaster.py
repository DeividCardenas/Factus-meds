import asyncio
from collections.abc import AsyncGenerator
from typing import Any


class InvoiceEventBroadcaster:
    """Thread-safe, in-process pub/sub broadcaster for invoice processing events."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[Any]] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: Any) -> None:
        async with self._lock:
            queues = list(self._subscribers)
        for queue in queues:
            await queue.put(event)

    async def subscribe(self) -> AsyncGenerator[Any, None]:
        queue: asyncio.Queue[Any] = asyncio.Queue()
        async with self._lock:
            self._subscribers.append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            async with self._lock:
                self._subscribers.remove(queue)
