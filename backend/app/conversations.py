from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthenticatedUser, get_current_user
from app.db import get_db
from app.models import Conversation, Message, OrganizationMember, Workspace, WorkspaceMember
from app.tenancy import get_authorized_conversation, require_workspace_access

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organization_id: uuid.UUID
    workspace_id: uuid.UUID
    title: str = Field(default="New conversation", min_length=1, max_length=300)


class ConversationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=300)
    status: str | None = Field(default=None, pattern="^(active|archived|deleted)$")


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(pattern="^(system|user|assistant|tool)$")
    content: str = Field(min_length=1, max_length=200000)
    provider: str | None = None
    model: str | None = None
    metadata: dict = Field(default_factory=dict)


def serialize_conversation(item: Conversation) -> dict:
    return {"id": str(item.id), "organization_id": str(item.organization_id), "workspace_id": str(item.workspace_id), "user_id": str(item.user_id), "title": item.title, "model_provider": item.model_provider, "model_name": item.model_name, "status": item.status, "created_at": item.created_at.isoformat() if item.created_at else None, "updated_at": item.updated_at.isoformat() if item.updated_at else None}


def serialize_message(item: Message) -> dict:
    return {"id": str(item.id), "conversation_id": str(item.conversation_id), "user_id": str(item.user_id) if item.user_id else None, "role": item.role, "content": item.content, "provider": item.provider, "model": item.model, "metadata": item.metadata_json or {}, "created_at": item.created_at.isoformat() if item.created_at else None}


@router.post("")
async def create_conversation(payload: ConversationCreate, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _, workspace, _ = await require_workspace_access(payload.workspace_id, user, db)
    if workspace.organization_id != payload.organization_id:
        raise HTTPException(status_code=403, detail="Workspace does not belong to organization")
    conversation = Conversation(organization_id=payload.organization_id, workspace_id=payload.workspace_id, user_id=user.id, title=payload.title)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return serialize_conversation(conversation)


@router.get("")
async def list_conversations(workspace_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db), limit: int = Query(default=50, ge=1, le=100), before: datetime | None = None):
    await require_workspace_access(workspace_id, user, db)
    query = select(Conversation).where(Conversation.workspace_id == workspace_id, Conversation.status != "deleted").order_by(desc(Conversation.updated_at)).limit(limit)
    if before:
        query = query.where(Conversation.updated_at < before)
    result = await db.execute(query)
    return {"items": [serialize_conversation(item) for item in result.scalars().all()], "next_before": None}


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return serialize_conversation(await get_authorized_conversation(conversation_id, user, db))


@router.patch("/{conversation_id}")
async def patch_conversation(conversation_id: uuid.UUID, payload: ConversationPatch, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await get_authorized_conversation(conversation_id, user, db)
    if payload.title is not None:
        item.title = payload.title
    if payload.status is not None:
        item.status = payload.status
    await db.commit()
    await db.refresh(item)
    return serialize_conversation(item)


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await get_authorized_conversation(conversation_id, user, db)
    item.status = "deleted"
    await db.commit()
    return {"deleted": True}


@router.get("/{conversation_id}/messages")
async def list_messages(conversation_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db), limit: int = Query(default=100, ge=1, le=200), before: datetime | None = None):
    await get_authorized_conversation(conversation_id, user, db)
    query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit)
    if before:
        query = query.where(Message.created_at < before)
    result = await db.execute(query)
    return {"items": [serialize_message(item) for item in reversed(result.scalars().all())], "next_before": None}


@router.post("/{conversation_id}/messages")
async def add_message(conversation_id: uuid.UUID, payload: MessageCreate, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conversation = await get_authorized_conversation(conversation_id, user, db)
    message = Message(conversation_id=conversation.id, user_id=user.id if payload.role in {"user", "tool"} else None, role=payload.role, content=payload.content, provider=payload.provider, model=payload.model, metadata_json=payload.metadata)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return serialize_message(message)
