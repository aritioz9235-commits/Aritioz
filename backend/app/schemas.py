from __future__ import annotations

import base64
import binascii

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter, field_validator

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_DATA_URL_CHARS = 7 * 1024 * 1024
SAFE_IMAGE_DATA_PREFIXES = (
    "data:image/jpeg;base64,",
    "data:image/png;base64,",
    "data:image/webp;base64,",
)
IMAGE_SIGNATURES = {
    "data:image/jpeg;base64,": lambda data: data.startswith(b"\xff\xd8\xff"),
    "data:image/png;base64,": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "data:image/webp;base64,": lambda data: len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP",
}


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=200000)
    provider: str = "auto"
    model: str | None = None
    system_prompt: str | None = Field(default=None, max_length=10000)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=1000, ge=1, le=65536)
    top_p: float = Field(default=0.95, gt=0, le=1)
    image_url: str | None = Field(default=None, max_length=MAX_IMAGE_DATA_URL_CHARS)
    reasoning_budget: int | None = Field(default=None, ge=1, le=65536)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value.startswith("data:"):
            prefix = next((item for item in SAFE_IMAGE_DATA_PREFIXES if value.startswith(item)), None)
            if prefix is None:
                raise ValueError("image must be a JPEG, PNG, or WebP data URL")
            try:
                decoded = base64.b64decode(value[len(prefix):], validate=True)
            except (binascii.Error, ValueError) as exc:
                raise ValueError("image data is not valid base64") from exc
            if not decoded or len(decoded) > MAX_IMAGE_BYTES:
                raise ValueError("image must be no larger than 5 MB")
            if not IMAGE_SIGNATURES[prefix](decoded):
                raise ValueError("image content does not match its declared type")
            return value

        parsed = TypeAdapter(HttpUrl).validate_python(value)
        if parsed.scheme != "https":
            raise ValueError("remote images must use HTTPS")
        return str(parsed)


class ChatResponse(BaseModel):
    success: bool = True
    provider: str
    model: str
    response: str
