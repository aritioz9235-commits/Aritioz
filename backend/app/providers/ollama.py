from __future__ import annotations

import httpx
import logging

from app.providers.base import ChatResult, ProviderError
from app.schemas import ChatRequest


class OllamaProvider:
    name = "ollama"

    def __init__(self, enabled: bool, model: str, base_url: str, timeout: float):
        self.enabled = enabled
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logging.getLogger("aritioz.ai.ollama")

    async def list_models(self) -> list[str]:
        if not self.enabled:
            self.logger.info("Ollama disabled; base_url=%s", self.base_url)
            return []
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 5), follow_redirects=False) as client:
                response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = [item["name"] for item in response.json().get("models", []) if item.get("name")]
            if self.model and self.model not in models:
                self.logger.warning(
                    "Ollama is reachable but configured model is missing: model=%s base_url=%s available_models=%s",
                    self.model,
                    self.base_url,
                    models,
                )
                return []
            self.logger.info("Ollama health check passed: base_url=%s model=%s", self.base_url, self.model or (models[0] if models else ""))
            return models
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            self.logger.warning("Ollama health check failed: base_url=%s reason=%s", self.base_url, type(exc).__name__)
            return []

    async def is_available(self) -> bool:
        models = await self.list_models()
        return bool(models and (not self.model or self.model in models))

    async def chat(self, request: ChatRequest) -> ChatResult:
        models = await self.list_models()
        model = request.model or self.model or (models[0] if models else "")
        if not model or model not in models:
            configured = self.model or model or "(none configured)"
            raise ProviderError(f"Ollama model is unavailable: {configured}", retryable=True)
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
