from __future__ import annotations

import re
import uuid

import httpx
from fastapi import HTTPException


SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_storage_path(workspace_id: uuid.UUID, name: str) -> str:
    clean = SAFE_NAME.sub("-", name).strip(".-")[:180] or "upload"
    return f"{workspace_id}/{uuid.uuid4()}/{clean}"


async def upload_to_supabase(settings, path: str, content: bytes, mime_type: str) -> str:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(status_code=503, detail="File storage is not configured")
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{settings.supabase_storage_bucket}/{path}"
    headers = {"Authorization": f"Bearer {settings.supabase_service_role_key}", "apikey": settings.supabase_service_role_key, "Content-Type": mime_type, "x-upsert": "false"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, content=content, headers=headers)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="File storage upload failed")
    return path


async def delete_from_supabase(settings, path: str) -> None:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{settings.supabase_storage_bucket}"
    headers = {"Authorization": f"Bearer {settings.supabase_service_role_key}", "apikey": settings.supabase_service_role_key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=15) as client:
        await client.request("DELETE", url, json={"prefixes": [path]}, headers=headers)
