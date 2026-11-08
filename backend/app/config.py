from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

PROJECT_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
PROJECT_LOCAL_ENV = Path(__file__).resolve().parents[2] / ".env.local"
ROOT_LOCAL_ENV = PROJECT_ROOT_ENV.with_name(".env.local")
# Local development values take precedence over shared root defaults; shell
# variables still win because neither call overrides the process environment.
load_dotenv(PROJECT_LOCAL_ENV, override=False)
load_dotenv(ROOT_LOCAL_ENV, override=False)
load_dotenv(PROJECT_ROOT_ENV, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_LOCAL_ENV), str(ROOT_LOCAL_ENV), str(PROJECT_ROOT_ENV), ".env", "../.env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "production"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    backend_base_url: str = ""
    workspace_root: str = ""
    database_url: str = ""
    content_data_source: str = "database"
    db_env: str = "staging"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    redis_url: str = ""
    redis_enabled: bool = True
    redis_cache_ttl_seconds: int = Field(default=60, ge=1, le=86400)
    embedding_provider: str = "none"
    embedding_model: str = ""
    embedding_dimensions: int = Field(default=1536, ge=1, le=4096)
    max_upload_bytes: int = Field(default=50 * 1024 * 1024, ge=1024, le=500 * 1024 * 1024)
    imagekit_url_endpoint: str = ""
    imagekit_private_key: str = ""
    imagekit_public_key: str = ""
    supabase_storage_bucket: str = "aritioz-files"

    ai_default_provider: str = "glm"
    ai_provider_order: str = "glm,qwen,deepseek,ollama"

    glm_api_key: str = ""
    glm_model: str = "glm-5.2"
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    qwen_api_key: str = ""
    qwen_model: str = "qwen-max"
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-reasoner"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

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

    @field_validator("glm_base_url", "qwen_base_url", "deepseek_base_url", "gemini_base_url", "nvidia_base_url", "ollama_base_url")
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

    @property
    def async_database_url(self) -> str:
        value = self.database_url.strip()
        if value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value[len("postgresql://"):]
        if value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value[len("postgres://"):]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
