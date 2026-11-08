from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthenticatedUser, get_current_user
from app.db import get_db
from app.models import Conversation, OrganizationMember, Workspace, WorkspaceMember


async def require_organization_member(
    organization_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[AuthenticatedUser, str]:
    result = await db.execute(select(OrganizationMember.role).where(and_(OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == user.id)))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=403, detail="Organization access denied")
    return user, role


async def require_workspace_access(
    workspace_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[AuthenticatedUser, Workspace, str]:
    workspace_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = workspace_result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=403, detail="Workspace access denied")
    organization_result = await db.execute(select(OrganizationMember.role).where(and_(OrganizationMember.organization_id == workspace.organization_id, OrganizationMember.user_id == user.id)))
    organization_role = organization_result.scalar_one_or_none()
    if organization_role is None:
        raise HTTPException(status_code=403, detail="Workspace access denied")
    if organization_role in {"owner", "admin"}:
        return user, workspace, organization_role
    member_result = await db.execute(select(WorkspaceMember.role).where(and_(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user.id)))
    workspace_role = member_result.scalar_one_or_none()
    if workspace_role is None:
        raise HTTPException(status_code=403, detail="Workspace access denied")
    return user, workspace, workspace_role


async def get_authorized_conversation(conversation_id: uuid.UUID, user: AuthenticatedUser, db: AsyncSession) -> Conversation:
    result = await db.execute(select(Conversation).join(OrganizationMember, OrganizationMember.organization_id == Conversation.organization_id).where(and_(Conversation.id == conversation_id, OrganizationMember.user_id == user.id, Conversation.status != "deleted")))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
