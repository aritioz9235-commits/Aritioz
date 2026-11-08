from __future__ import annotations

import httpx

from app.providers.base import ChatResult, ProviderError
from app.schemas import ChatRequest


class OpenAICompatibleProvider:
    """Adapter for hosted APIs exposing the OpenAI chat-completions contract."""

    def __init__(self, name: str, api_key: str, model: str, base_url: str, timeout: float):
        self.name, self.api_key, self.model = name, api_key, model
        self.base_url, self.timeout = base_url.rstrip("/"), timeout

    async def is_available(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    async def list_models(self) -> list[str]:
        return [self.model] if await self.is_available() else []

    async def chat(self, request: ChatRequest) -> ChatResult:
        model = request.model or self.model
        if not self.api_key or not model:
            raise ProviderError(f"{self.name} is not configured", retryable=True)
        messages = ([{"role": "system", "content": request.system_prompt}] if request.system_prompt else [])
        messages.append({"role": "user", "content": request.message})
        body = {"model": model, "messages": messages, "temperature": request.temperature,
                "top_p": request.top_p, "max_tokens": request.max_tokens, "stream": False}
        if request.reasoning_budget is not None:
            body["reasoning_budget"] = request.reasoning_budget
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = await client.post(f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"}, json=body)
            if response.status_code in (401, 403):
                raise ProviderError(f"{self.name} authentication failed", retryable=False, status_code=502)
            if response.status_code == 429 or response.status_code >= 500:
                raise ProviderError(f"{self.name} is temporarily unavailable", retryable=True)
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"].strip()
            if not text:
                raise ProviderError(f"{self.name} returned no text", retryable=True)
            return ChatResult(self.name, model, text)
        except ProviderError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.name} request failed", retryable=True) from exc
