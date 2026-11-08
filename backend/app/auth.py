from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: uuid.UUID
    auth_user_id: uuid.UUID
    email: str
    display_name: str | None = None


def _token_from(credentials: HTTPAuthorizationCredentials | None) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return credentials.credentials


async def _decode(token: str, request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    try:
        if settings.supabase_jwt_secret:
            return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated")
        if settings.supabase_url:
            # Supabase publishes rotating signing keys; cache them briefly on the app instance.
            now = time.time()
            cached = getattr(request.app.state, "supabase_jwks", None)
            if not cached or cached[0] <= now:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json")
                    response.raise_for_status()
                cached = (now + 3600, response.json())
                request.app.state.supabase_jwks = cached
            header = jwt.get_unverified_header(token)
            key = next(item for item in cached[1].get("keys", []) if item.get("kid") == header.get("kid"))
            return jwt.decode(token, jwt.algorithms.RSAAlgorithm.from_jwk(key), algorithms=["RS256"], audience="authenticated")
    except (jwt.PyJWTError, httpx.HTTPError, StopIteration, KeyError, ValueError):
        pass
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    claims = await _decode(_token_from(credentials), request)
    subject = claims.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    try:
        auth_user_id = uuid.UUID(subject)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc
    result = await db.execute(select(User).where(User.auth_user_id == auth_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(auth_user_id=auth_user_id, email=str(claims.get("email", "")), display_name=claims.get("user_metadata", {}).get("full_name") if isinstance(claims.get("user_metadata"), dict) else None)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return AuthenticatedUser(id=user.id, auth_user_id=user.auth_user_id, email=user.email, display_name=user.display_name)
