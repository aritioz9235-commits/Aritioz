from __future__ import annotations

import json

import httpx
import pytest

from app.config import Settings
from app.main import create_app
from app.providers.base import ChatResult, ProviderError
from app.schemas import ChatRequest


class StubProvider:
    def __init__(self, name: str, *, result: ChatResult | None = None, error: Exception | None = None):
        self.name = name
        self._result = result
        self._error = error

    async def is_available(self) -> bool:
        return self._error is None

    async def list_models(self) -> list[str]:
        return [self._result.model] if self._result else []

    async def chat(self, request):
        if self._error:
            raise self._error
        assert self._result is not None
        return self._result


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="test",
        allowed_origins="http://localhost:3000",
        ai_default_provider="gemini",
        ai_provider_order="gemini,nvidia,ollama",
        max_input_chars=100,
        rate_limit_requests=100,
        rate_limit_window_seconds=60,
    )


def test_multimodal_nvidia_fields_are_validated() -> None:
    request = ChatRequest(
        message="What is in this image?",
        provider="nvidia",
        image_url="https://assets.example.com/example.jpg",
        reasoning_budget=16384,
        max_tokens=65536,
        top_p=0.95,
    )
    assert str(request.image_url) == "https://assets.example.com/example.jpg"
    assert request.reasoning_budget == 16384
    assert request.top_p == 0.95


def test_image_data_urls_allow_safe_types_and_reject_unsafe_types() -> None:
    request = ChatRequest(message="Describe it", image_url="data:image/png;base64,iVBORw0KGgo=")
    assert request.image_url == "data:image/png;base64,iVBORw0KGgo="

    with pytest.raises(ValueError, match="JPEG, PNG, or WebP"):
        ChatRequest(message="Describe it", image_url="data:image/svg+xml;base64,PHN2Zy8+")

    with pytest.raises(ValueError, match="does not match"):
        ChatRequest(message="Describe it", image_url="data:image/png;base64,aGVsbG8=")


@pytest.mark.anyio
async def test_health(settings: Settings) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(settings=settings, providers={})),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"message": ""}, 422),
        ({"message": "x" * 101}, 422),
        ({"message": "hello", "temperature": 3}, 422),
        ({"message": "hello", "max_tokens": 0}, 422),
    ],
)
async def test_chat_validates_requests(settings: Settings, payload: dict, expected_status: int) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(settings=settings, providers={})),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/chat", json=payload)
    assert response.status_code == expected_status


@pytest.mark.anyio
async def test_rejects_unsupported_provider(settings: Settings) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(settings=settings, providers={})),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/chat", json={"message": "hello", "provider": "unknown"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_PROVIDER"


@pytest.mark.anyio
async def test_rejects_image_for_provider_without_image_support(settings: Settings) -> None:
    providers = {
        "gemini": StubProvider("gemini", result=ChatResult("gemini", "configured", "text-only answer")),
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(settings=settings, providers=providers)),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/chat",
            json={
                "message": "Describe it",
                "provider": "gemini",
                "image_url": "data:image/png;base64,iVBORw0KGgo=",
            },
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_INPUT"


@pytest.mark.anyio
async def test_auto_provider_falls_back_on_temporary_failure(settings: Settings) -> None:
    providers = {
        "gemini": StubProvider("gemini", error=ProviderError("temporary secret detail", retryable=True)),
        "nvidia": StubProvider("nvidia", result=ChatResult("nvidia", "nemotron", "fallback answer")),
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(settings=settings, providers=providers)),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "provider": "nvidia",
        "model": "nemotron",
        "response": "fallback answer",
    }


@pytest.mark.anyio
async def test_provider_unavailable_error_hides_secrets(settings: Settings) -> None:
    providers = {
        "gemini": StubProvider("gemini", error=ProviderError("key=super-secret https://internal", retryable=True)),
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(settings=settings, providers=providers)),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/chat", json={"message": "hello"})
    body = json.dumps(response.json())
    assert response.status_code == 503
    assert "super-secret" not in body
    assert "internal" not in body
    assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"


@pytest.mark.anyio
async def test_models_only_returns_available_models(settings: Settings) -> None:
    providers = {
        "gemini": StubProvider("gemini", result=ChatResult("gemini", "gemini-configured", "ok")),
        "ollama": StubProvider("ollama", error=ProviderError("offline", retryable=True)),
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(settings=settings, providers=providers)),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/models")
    assert response.status_code == 200
    assert response.json() == {"providers": [{"provider": "gemini", "models": ["gemini-configured"]}]}
