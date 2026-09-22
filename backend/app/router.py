from __future__ import annotations

import logging

from app.config import Settings
from app.providers.base import AIProvider, ChatResult, ProviderError
from app.schemas import ChatRequest

logger = logging.getLogger("aritioz.ai")


class ProviderRouter:
    def __init__(self, settings: Settings, providers: dict[str, AIProvider]):
        self.settings = settings
        self.providers = providers

    async def available_models(self) -> list[dict[str, object]]:
        output = []
        for name in self.settings.provider_order:
            provider = self.providers.get(name)
            if not provider:
                continue
            models = await provider.list_models()
            if models:
                output.append({"provider": name, "models": models})
        return output

    async def chat(self, request: ChatRequest) -> ChatResult:
        explicit = request.provider != "auto"
        if explicit:
            if request.provider not in self.providers:
                raise ProviderError("Unsupported provider", retryable=False, status_code=400)
            candidates = [request.provider]
        else:
            order = self.settings.provider_order
            default = self.settings.ai_default_provider.strip().lower()
            candidates = [default, *[name for name in order if name != default]]

        last_error: ProviderError | None = None
        for name in candidates:
            provider = self.providers.get(name)
            if not provider:
                continue
            try:
                if request.image_url and name != "nvidia":
                    if explicit:
                        raise ProviderError("Provider does not support image input", retryable=False, status_code=400)
                    continue
                models = await provider.list_models()
                if request.model and request.model not in models:
                    if explicit:
                        raise ProviderError("Unsupported model", retryable=False, status_code=400)
                    continue
                return await provider.chat(request)
            except ProviderError as exc:
                last_error = exc
                logger.warning("AI provider %s failed (retryable=%s)", name, exc.retryable)
                if explicit or not exc.retryable:
                    raise
        raise last_error or ProviderError("No configured AI provider is available", retryable=True)
