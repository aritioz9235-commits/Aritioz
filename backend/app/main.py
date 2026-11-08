from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi import Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.auth import AuthenticatedUser, get_current_user
from app.conversations import router as conversations_router
from app.files import router as files_router
from app.rag import router as rag_router
from app.db import build_session_factory
from app.db import get_db
from app.models import Message, UsageLog
from app.tenancy import get_authorized_conversation
from app.providers import build_providers
from app.providers.base import AIProvider, ProviderError
from app.rate_limit import InMemoryRateLimiter, RedisRateLimiter
from app.router import ProviderRouter
from app.schemas import ChatRequest, ChatResponse
from app.workspace import router as workspace_router
from app.resources import router as resources_router
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def create_app(settings: Settings | None = None, providers: Mapping[str, AIProvider] | None = None) -> FastAPI:
    config = settings or get_settings()
    provider_map = dict(providers) if providers is not None else build_providers(config)
    router = ProviderRouter(config, provider_map)
    limiter = RedisRateLimiter(config.redis_url, config.rate_limit_requests, config.rate_limit_window_seconds) if config.redis_enabled and config.redis_url else InMemoryRateLimiter(config.rate_limit_requests, config.rate_limit_window_seconds)
    app = FastAPI(title="Aritioz AI API", version="1.0.0", docs_url=None if config.app_env == "production" else "/docs")
    app.state.settings = config
    app.state.session_factory = build_session_factory(config.async_database_url)
    app.include_router(workspace_router)
    app.include_router(conversations_router)
    app.include_router(files_router)
    app.include_router(rag_router)
    app.include_router(resources_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.on_event("startup")
    async def log_provider_status() -> None:
        configured = config.provider_order
        logger = logging.getLogger("aritioz.ai")
        logger.info("Configured AI providers: order=%s default=%s", configured, config.ai_default_provider)
        available: list[str] = []
        for name in configured:
            provider = provider_map.get(name)
            if provider is None:
                continue
            try:
                if await provider.list_models():
                    available.append(name)
            except Exception:
                logger.exception("Provider startup check failed: provider=%s", name)
        logger.info("Available AI providers at startup: %s", available)

    @app.middleware("http")
    async def request_safeguards(request: Request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length and content_length.isdigit() and int(content_length) > config.max_request_bytes:
                return error_response(413, "REQUEST_TOO_LARGE", "Request body is too large")
            if len(await request.body()) > config.max_request_bytes:
                return error_response(413, "REQUEST_TOO_LARGE", "Request body is too large")
            client_key = request.client.host if request.client else "unknown"
            if not await limiter.allow(client_key):
                return error_response(429, "RATE_LIMITED", "Too many requests; try again shortly")
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError):
        return error_response(422, "INVALID_REQUEST", "Request validation failed")

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception):
        logging.getLogger("aritioz.api").exception("Unhandled API error", exc_info=exc)
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/database")
    async def database_health() -> dict[str, object]:
        factory = app.state.session_factory
        if factory is None:
            return {"status": "unavailable", "database": "not_configured"}
        try:
            async with factory() as session:
                now = (await session.execute(text("SELECT NOW()"))).scalar_one()
            return {"status": "ok", "database": "connected", "server_time": now.isoformat()}
        except Exception:
            logging.getLogger("aritioz.database").exception("Database health check failed")
            return {"status": "error", "database": "unavailable"}

    @app.get("/api/models")
    async def models() -> dict[str, object]:
        return {"providers": await router.available_models()}

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(payload: ChatRequest):
        if len(payload.message) > config.max_input_chars:
            return error_response(422, "INVALID_REQUEST", "Message is too long")
        try:
            result = await router.chat(payload)
        except ProviderError as exc:
            if exc.status_code == 400:
                message = str(exc).lower()
                code = (
                    "UNSUPPORTED_INPUT"
                    if "image" in message
                    else "UNSUPPORTED_PROVIDER"
                    if "provider" in message
                    else "UNSUPPORTED_MODEL"
                )
                return error_response(400, code, str(exc))
            return error_response(503 if exc.retryable else 502, "PROVIDER_UNAVAILABLE", "No AI provider is currently available")
        return ChatResponse(provider=result.provider, model=result.model, response=result.response)

    @app.post("/api/conversations/{conversation_id}/chat", response_model=ChatResponse)
    async def persistent_chat(
        conversation_id: uuid.UUID,
        payload: ChatRequest,
        user: AuthenticatedUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        conversation = await get_authorized_conversation(conversation_id, user, db)
        started = time.perf_counter()
        user_message = Message(conversation_id=conversation.id, user_id=user.id, role="user", content=payload.message, metadata_json={})
        db.add(user_message)
        await db.commit()
        try:
            result = await router.chat(payload)
        except ProviderError as exc:
            db.add(UsageLog(organization_id=conversation.organization_id, workspace_id=conversation.workspace_id, user_id=user.id, conversation_id=conversation.id, provider=payload.provider, model=payload.model or "auto", operation="chat", latency_ms=round((time.perf_counter() - started) * 1000), success=False, error_code="PROVIDER_UNAVAILABLE", metadata_json={}))
            await db.commit()
            if exc.status_code == 400:
                return error_response(400, "UNSUPPORTED_PROVIDER", str(exc))
            return error_response(503 if exc.retryable else 502, "PROVIDER_UNAVAILABLE", "No AI provider is currently available")
        db.add(Message(conversation_id=conversation.id, user_id=None, role="assistant", content=result.response, provider=result.provider, model=result.model, metadata_json={}))
        db.add(UsageLog(organization_id=conversation.organization_id, workspace_id=conversation.workspace_id, user_id=user.id, conversation_id=conversation.id, provider=result.provider, model=result.model, operation="chat", latency_ms=round((time.perf_counter() - started) * 1000), success=True, metadata_json={}))
        conversation.model_provider = result.provider
        conversation.model_name = result.model
        await db.commit()
        return ChatResponse(provider=result.provider, model=result.model, response=result.response)

    return app


app = create_app()
