from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def build_session_factory(database_url: str) -> async_sessionmaker[AsyncSession] | None:
    if not database_url.strip():
        return None
    engine = create_async_engine(database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise RuntimeError("Database is not configured")
    async with factory() as session:
        yield session


def jsonable_metadata(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
