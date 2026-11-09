from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import uuid
from dataclasses import dataclass

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import AuthResponse, AuthUserResponse, LoginRequest, SignUpRequest

bearer = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/api/auth", tags=["auth"])
PASSWORD_ITERATIONS = 600_000


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
    if settings.jwt_secret:
        try:
            return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], audience="aritioz-api")
        except jwt.PyJWTError:
            # It may be a legacy Supabase token, which is checked below.
            pass
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


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def _verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        scheme, iterations, encoded_salt, encoded_digest = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), base64.b64decode(encoded_salt), int(iterations)
        )
        return hmac.compare_digest(digest, base64.b64decode(encoded_digest))
    except (ValueError, TypeError):
        return False


def _issue_token(user: User, request: Request) -> str:
    settings = request.app.state.settings
    if not settings.jwt_secret:
        raise HTTPException(status_code=503, detail="JWT authentication is not configured")
    now = int(time.time())
    return jwt.encode(
        {
            "sub": str(user.auth_user_id),
            "email": user.email,
            "aud": "aritioz-api",
            "iat": now,
            "exp": now + settings.jwt_access_token_expire_minutes * 60,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def _auth_response(user: User, request: Request) -> AuthResponse:
    return AuthResponse(
        access_token=_issue_token(user, request),
        user=AuthUserResponse(id=user.id, email=user.email, display_name=user.display_name),
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignUpRequest, request: Request, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    existing = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    user = User(
        auth_user_id=uuid.uuid4(),
        email=payload.email,
        display_name=payload.name,
        password_hash=_hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _auth_response(user, request)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    user = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if user is None or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _auth_response(user, request)


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


@router.get("/me", response_model=AuthUserResponse)
async def me(user: AuthenticatedUser = Depends(get_current_user)) -> AuthUserResponse:
    return AuthUserResponse(id=user.id, email=user.email, display_name=user.display_name)
