from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthenticatedUser, get_current_user
from app.db import get_db
from app.tenancy import require_workspace_access

router = APIRouter(prefix="/api/rag", tags=["rag"])


def chunk_text(content: str, size: int = 1200, overlap: int = 160) -> list[str]:
    if size <= overlap:
        raise ValueError("chunk size must be greater than overlap")
    return [content[start:start + size] for start in range(0, len(content), size - overlap) if content[start:start + size].strip()]


class VectorSearchRequest(BaseModel):
    workspace_id: uuid.UUID
    embedding: list[float] = Field(min_length=1, max_length=4096)
    limit: int = Field(default=5, ge=1, le=20)


@router.post("/search")
async def vector_search(payload: VectorSearchRequest, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _, workspace, _ = await require_workspace_access(payload.workspace_id, user, db)
    # Both predicates are intentional: workspace access alone must never widen a vector query.
    result = await db.execute(text("""
        SELECT id, content, metadata, 1 - (embedding <=> CAST(:embedding AS vector)) AS score
        FROM document_chunks
        WHERE organization_id = :organization_id AND workspace_id = :workspace_id AND embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """), {"embedding": "[" + ",".join(str(value) for value in payload.embedding) + "]", "organization_id": str(workspace.organization_id), "workspace_id": str(payload.workspace_id), "limit": payload.limit})
    return {"items": [dict(row) for row in result.mappings().all()]}
