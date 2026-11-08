from __future__ import annotations

import json
from typing import Any


class OptionalRedis:
    """Best-effort Redis facade; local development remains usable without Redis."""

    def __init__(self, url: str, enabled: bool = True):
        self._client = None
        if enabled and url:
            try:
                import redis.asyncio as redis
                self._client = redis.from_url(url, decode_responses=True)
            except ImportError:
                self._client = None

    async def get_json(self, key: str) -> Any | None:
        if self._client is None:
            return None
        try:
            value = await self._client.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    async def set_json(self, key: str, value: Any, ttl: int) -> bool:
        if self._client is None:
            return False

    async def enqueue(self, queue: str, payload: dict[str, Any]) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.rpush(queue, json.dumps(payload))
            return True
        except Exception:
            return False

    async def dequeue(self, queue: str, timeout: int = 1) -> dict[str, Any] | None:
        if self._client is None:
            return None
        try:
            item = await self._client.blpop(queue, timeout=timeout)
            return json.loads(item[1]) if item else None
        except Exception:
            return None
        try:
            await self._client.set(key, json.dumps(value), ex=ttl)
            return True
        except Exception:
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
