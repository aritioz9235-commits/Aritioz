from __future__ import annotations

import httpx

from app.providers.base import ChatResult, ProviderError
from app.schemas import ChatRequest


class OllamaProvider:
    name = "ollama"

    def __init__(self, enabled: bool, model: str, base_url: str, timeout: float):
        self.enabled = enabled
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    async def list_models(self) -> list[str]:
        if not self.enabled:
            return []
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 5), follow_redirects=False) as client:
                response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return [item["name"] for item in response.json().get("models", []) if item.get("name")]
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

    async def is_available(self) -> bool:
        models = await self.list_models()
        return bool(models and (not self.model or self.model in models))

    async def chat(self, request: ChatRequest) -> ChatResult:
        models = await self.list_models()
        model = request.model or self.model or (models[0] if models else "")
        if not model or model not in models:
            raise ProviderError("Ollama model is unavailable", retryable=True)
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.message})
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": request.temperature, "num_predict": request.max_tokens},
                    },
                )
            if response.status_code >= 500:
                raise ProviderError("Ollama is temporarily unavailable", retryable=True)
            response.raise_for_status()
            text = response.json()["message"]["content"].strip()
            if not text:
                raise ProviderError("Ollama returned no text", retryable=True)
            return ChatResult(self.name, model, text)
        except ProviderError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise ProviderError("Ollama request failed", retryable=True) from exc
