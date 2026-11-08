from __future__ import annotations

from app.config import Settings
from app.providers.base import AIProvider
from app.providers.gemini import GeminiProvider
from app.providers.nvidia import NvidiaProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai_compatible import OpenAICompatibleProvider


def build_providers(settings: Settings) -> dict[str, AIProvider]:
    return {
        "glm": OpenAICompatibleProvider("glm", settings.glm_api_key, settings.glm_model, settings.glm_base_url, settings.request_timeout_seconds),
        "qwen": OpenAICompatibleProvider("qwen", settings.qwen_api_key, settings.qwen_model, settings.qwen_base_url, settings.request_timeout_seconds),
        "deepseek": OpenAICompatibleProvider("deepseek", settings.deepseek_api_key, settings.deepseek_model, settings.deepseek_base_url, settings.request_timeout_seconds),
        "gemini": GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.gemini_base_url, settings.request_timeout_seconds),
        "nvidia": NvidiaProvider(settings.nvidia_api_key, settings.nvidia_model, settings.nvidia_base_url, settings.request_timeout_seconds),
        "ollama": OllamaProvider(settings.ollama_enabled, settings.ollama_model, settings.ollama_base_url, settings.request_timeout_seconds),
    }
