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


class RedisRateLimiter:
    """Atomic fixed-window limiter with an in-memory fallback when Redis is unavailable."""

    def __init__(self, url: str, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._fallback = InMemoryRateLimiter(limit, window_seconds)
        try:
            import redis.asyncio as redis
            self._client = redis.from_url(url, decode_responses=True)
        except ImportError:
            self._client = None

    async def allow(self, key: str) -> bool:
        if self._client is None:
            return await self._fallback.allow(key)
        redis_key = f"aritioz:ratelimit:{key}"
        try:
            count = await self._client.incr(redis_key)
            if count == 1:
                await self._client.expire(redis_key, self.window_seconds)
            return count <= self.limit
        except Exception:
            return await self._fallback.allow(key)
