from __future__ import annotations

import logging
from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.providers import build_providers
from app.providers.base import AIProvider, ProviderError
from app.rate_limit import InMemoryRateLimiter
from app.router import ProviderRouter
from app.schemas import ChatRequest, ChatResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def create_app(settings: Settings | None = None, providers: Mapping[str, AIProvider] | None = None) -> FastAPI:
    config = settings or get_settings()
    provider_map = dict(providers) if providers is not None else build_providers(config)
    router = ProviderRouter(config, provider_map)
    limiter = InMemoryRateLimiter(config.rate_limit_requests, config.rate_limit_window_seconds)
    app = FastAPI(title="Aritioz AI API", version="1.0.0", docs_url=None if config.app_env == "production" else "/docs")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

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

    return app


app = create_app()
