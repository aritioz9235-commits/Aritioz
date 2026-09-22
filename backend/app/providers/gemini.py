from __future__ import annotations

import httpx

from app.providers.base import ChatResult, ProviderError
from app.schemas import ChatRequest


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    async def is_available(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    async def list_models(self) -> list[str]:
        return [self.model] if await self.is_available() else []

    async def chat(self, request: ChatRequest) -> ChatResult:
        model = request.model or self.model
        if not self.api_key or not model or not self.base_url:
            raise ProviderError("Gemini is not configured", retryable=True)
        body: dict = {
            "contents": [{"role": "user", "parts": [{"text": request.message}]}],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        if request.system_prompt:
            body["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = await client.post(
                    f"{self.base_url}/models/{model}:generateContent",
                    headers={"x-goog-api-key": self.api_key},
                    json=body,
                )
            if response.status_code in (401, 403):
                raise ProviderError("Gemini authentication failed", retryable=False, status_code=502)
            if response.status_code == 429 or response.status_code >= 500:
                raise ProviderError("Gemini is temporarily unavailable", retryable=True)
            response.raise_for_status()
            payload = response.json()
            text = "".join(
                part.get("text", "")
                for candidate in payload.get("candidates", [])[:1]
                for part in candidate.get("content", {}).get("parts", [])
            ).strip()
            if not text:
                raise ProviderError("Gemini returned no text", retryable=True)
            return ChatResult(self.name, model, text)
        except ProviderError:
            raise
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise ProviderError("Gemini request failed", retryable=True) from exc
