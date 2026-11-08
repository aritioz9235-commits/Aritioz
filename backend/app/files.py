from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File as FormFile, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthenticatedUser, get_current_user
from app.db import get_db
from app.models import File
from app.storage import delete_from_supabase, safe_storage_path, upload_to_supabase
from app.tenancy import require_workspace_access

router = APIRouter(prefix="/api/files", tags=["files"])
ALLOWED_TYPES = {"application/pdf", "text/plain", "text/markdown", "application/json", "image/jpeg", "image/png", "image/webp", "video/mp4"}


def serialize_file(item: File) -> dict:
    return {"id": str(item.id), "workspace_id": str(item.workspace_id), "original_name": item.original_name, "mime_type": item.mime_type, "size_bytes": item.size_bytes, "provider": item.provider, "status": item.status, "created_at": item.created_at.isoformat() if item.created_at else None}


@router.post("")
async def upload_file(request: Request, workspace_id: uuid.UUID, upload: UploadFile = FormFile(...), user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _, workspace, _ = await require_workspace_access(workspace_id, user, db)
    mime_type = upload.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type")
    content = await upload.read()
    if len(content) > request.app.state.settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File is too large")
    path = safe_storage_path(workspace_id, upload.filename or "upload")
    await upload_to_supabase(request.app.state.settings, path, content, mime_type)
    item = File(organization_id=workspace.organization_id, workspace_id=workspace_id, uploaded_by=user.id, provider="supabase", storage_path=path, original_name=upload.filename or "upload", mime_type=mime_type, size_bytes=len(content), metadata_json={})
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return serialize_file(item)


@router.get("")
async def list_files(workspace_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_workspace_access(workspace_id, user, db)
    result = await db.execute(select(File).where(File.workspace_id == workspace_id).order_by(File.created_at.desc()))
    return {"items": [serialize_file(item) for item in result.scalars().all()]}


@router.delete("/{file_id}")
async def delete_file(request: Request, file_id: uuid.UUID, user: AuthenticatedUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(File).where(File.id == file_id, File.uploaded_by == user.id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="File not found")
    await require_workspace_access(item.workspace_id, user, db)
    await delete_from_supabase(request.app.state.settings, item.storage_path)
    await db.delete(item)
    await db.commit()
    return {"deleted": True}
