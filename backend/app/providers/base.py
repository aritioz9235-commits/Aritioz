from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.schemas import ChatRequest


@dataclass(frozen=True)
class ChatResult:
    provider: str
    model: str
    response: str


class ProviderError(Exception):
    def __init__(self, message: str, *, retryable: bool, status_code: int = 503):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


class AIProvider(Protocol):
    name: str

    async def is_available(self) -> bool: ...
    async def list_models(self) -> list[str]: ...
    async def chat(self, request: ChatRequest) -> ChatResult: ...
