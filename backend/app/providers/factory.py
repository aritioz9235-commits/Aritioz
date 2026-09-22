from __future__ import annotations

from app.config import Settings
from app.providers.base import AIProvider
from app.providers.gemini import GeminiProvider
from app.providers.nvidia import NvidiaProvider
from app.providers.ollama import OllamaProvider


def build_providers(settings: Settings) -> dict[str, AIProvider]:
    return {
        "gemini": GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.gemini_base_url, settings.request_timeout_seconds),
        "nvidia": NvidiaProvider(settings.nvidia_api_key, settings.nvidia_model, settings.nvidia_base_url, settings.request_timeout_seconds),
        "ollama": OllamaProvider(settings.ollama_enabled, settings.ollama_model, settings.ollama_base_url, settings.request_timeout_seconds),
    }
