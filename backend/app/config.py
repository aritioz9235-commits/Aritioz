from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "production"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    backend_base_url: str = ""

    ai_default_provider: str = "gemini"
    ai_provider_order: str = "gemini,nvidia,ollama"

    gemini_api_key: str = ""
    gemini_model: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = ""

    ollama_enabled: bool = True
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""

    request_timeout_seconds: float = Field(default=60, gt=0, le=300)
    max_input_chars: int = Field(default=30000, ge=1, le=200000)
    max_request_bytes: int = Field(default=8 * 1024 * 1024, ge=1024, le=16 * 1024 * 1024)
    rate_limit_requests: int = Field(default=30, ge=1, le=10000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    trust_proxy_headers: bool = False

    @field_validator("gemini_base_url", "nvidia_base_url", "ollama_base_url")
    @classmethod
    def validate_server_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized:
            return ""
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("provider URL must use http or https")
        return normalized

    @property
    def provider_order(self) -> list[str]:
        return list(dict.fromkeys(part.strip().lower() for part in self.ai_provider_order.split(",") if part.strip()))

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        if "*" in origins:
            raise ValueError("wildcard CORS is not allowed")
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
