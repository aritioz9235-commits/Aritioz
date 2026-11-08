from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthenticatedUser, get_current_user
from app.db import get_db
from app.models import AIAgent, Project, Task, Workspace
from app.tenancy import require_workspace_access

router = APIRouter(tags=["resources"])


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or str(uuid.uuid4())


def public(item: Any) -> dict[str, Any]:
    data = {column.name: getattr(item, column.name) for column in item.__table__.columns}
    for key, value in data.items():
        if isinstance(value, uuid.UUID):
            data[key] = str(value)
        elif hasattr(value, "isoformat"):
            data[key] = value.isoformat()
    return data


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=10000)


class ProjectPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(default=None, pattern="^(active|archived)$")


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(default="todo", pattern="^(todo|in_progress|done|cancelled)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")


class TaskPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(default=None, pattern="^(todo|in_progress|done|cancelled)$")
    priority: str | None = Field(default=None, pattern="^(low|medium|high|urgent)$")
    project_id: uuid.UUID | None = None


class AgentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    provider: str = Field(default="auto", max_length=100)
    model: str | None = Field(default=None, max_length=200)
    instructions: str | None = Field(default=None, max_length=30000)


class AgentPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    provider: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=200)
    instructions: str | None = Field(default=None, max_length=30000)
    status: str | None = Field(default=None, pattern="^(active|archived)$")


async def workspace_for(workspace_id: uuid.UUID, user: AuthenticatedUser, db: AsyncSession) -> Workspace:
    return (await require_workspace_access(workspace_id, user, db))[1]


async def project_for(project_id: uuid.UUID, user: AuthenticatedUser, db: AsyncSession) -> Project:
    item = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if item is None:
        raise HTTPException(404, "Project not found")
    await workspace_for(item.workspace_id, user, db)
    return item


async def task_for(task_id: uuid.UUID, user: AuthenticatedUser, db: AsyncSession) -> Task:
    item = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
    if item is None:
        raise HTTPException(404, "Task not found")
    await workspace_for(item.workspace_id, user, db)
    return item


async def agent_for(agent_id: uuid.UUID, user: AuthenticatedUser, db: AsyncSession) -> AIAgent:
    item = (await db.execute(select(AIAgent).where(AIAgent.id == agent_id))).scalar_one_or_none()
    if item is None:
        raise HTTPException(404, "Agent not found")
    await workspace_for(item.workspace_id, user, db)
    return item


@router.get("/api/projects")
async def list_projects(workspace_id: uuid.UUID = Query(...), user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await workspace_for(workspace_id, user, db)
    result = await db.execute(select(Project).where(Project.workspace_id == workspace_id, Project.status != "archived").order_by(Project.created_at.desc()))
    return {"items": [public(item) for item in result.scalars().all()]}


@router.post("/api/projects")
async def create_project(payload: ProjectCreate, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    workspace = await workspace_for(payload.workspace_id, user, db)
    item = Project(organization_id=workspace.organization_id, workspace_id=workspace.id, created_by=user.id, name=payload.name, slug=payload.slug or slugify(payload.name), description=payload.description)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return public(item)


@router.get("/api/projects/{project_id}")
async def get_project(project_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return public(await project_for(project_id, user, db))


@router.patch("/api/projects/{project_id}")
async def patch_project(project_id: uuid.UUID, payload: ProjectPatch, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await project_for(project_id, user, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return public(item)


@router.delete("/api/projects/{project_id}")
async def delete_project(project_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await project_for(project_id, user, db)
    await db.delete(item)
    await db.commit()
    return {"deleted": True}


@router.get("/api/tasks")
async def list_tasks(workspace_id: uuid.UUID = Query(...), user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await workspace_for(workspace_id, user, db)
    result = await db.execute(select(Task).where(Task.workspace_id == workspace_id).order_by(Task.created_at.desc()))
    return {"items": [public(item) for item in result.scalars().all()]}


@router.post("/api/tasks")
async def create_task(payload: TaskCreate, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    workspace = await workspace_for(payload.workspace_id, user, db)
    if payload.project_id:
        project = await project_for(payload.project_id, user, db)
        if project.workspace_id != workspace.id:
            raise HTTPException(400, "Project does not belong to the workspace")
    item = Task(organization_id=workspace.organization_id, workspace_id=workspace.id, project_id=payload.project_id, created_by=user.id, title=payload.title, description=payload.description, status=payload.status, priority=payload.priority)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return public(item)


@router.patch("/api/tasks/{task_id}")
async def patch_task(task_id: uuid.UUID, payload: TaskPatch, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await task_for(task_id, user, db)
    data = payload.model_dump(exclude_unset=True)
    if "project_id" in data and data["project_id"]:
        project = await project_for(data["project_id"], user, db)
        if project.workspace_id != item.workspace_id:
            raise HTTPException(400, "Project does not belong to the task workspace")
    for key, value in data.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return public(item)


@router.delete("/api/tasks/{task_id}")
async def delete_task(task_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await task_for(task_id, user, db)
    await db.delete(item)
    await db.commit()
    return {"deleted": True}


@router.get("/api/agents")
async def list_agents(workspace_id: uuid.UUID = Query(...), user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await workspace_for(workspace_id, user, db)
    result = await db.execute(select(AIAgent).where(AIAgent.workspace_id == workspace_id, AIAgent.status != "archived").order_by(AIAgent.created_at.desc()))
    return {"items": [public(item) for item in result.scalars().all()]}


@router.post("/api/agents")
async def create_agent(payload: AgentCreate, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    workspace = await workspace_for(payload.workspace_id, user, db)
    item = AIAgent(organization_id=workspace.organization_id, workspace_id=workspace.id, created_by=user.id, **payload.model_dump(exclude={"workspace_id"}))
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return public(item)


@router.get("/api/agents/{agent_id}")
async def get_agent(agent_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return public(await agent_for(agent_id, user, db))


@router.patch("/api/agents/{agent_id}")
async def patch_agent(agent_id: uuid.UUID, payload: AgentPatch, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await agent_for(agent_id, user, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return public(item)


@router.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await agent_for(agent_id, user, db)
    await db.delete(item)
    await db.commit()
    return {"deleted": True}
