from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        async with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
            if len(timestamps) >= self.limit:
                return False
            timestamps.append(now)
            return True
