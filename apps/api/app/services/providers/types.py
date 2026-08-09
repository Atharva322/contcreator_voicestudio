from __future__ import annotations

from enum import Enum
from typing import Protocol


class ProviderFailureCategory(str, Enum):
    timeout = "timeout"
    connection = "connection"
    rate_limit = "rate_limit"
    provider_temporary = "provider_temporary"
    empty_response = "empty_response"
    invalid_json = "invalid_json"
    invalid_shape = "invalid_shape"


class ProviderFailure(Exception):
    def __init__(self, category: ProviderFailureCategory, message: str) -> None:
        super().__init__(message)
        self.category = category


class JsonGenerationProvider(Protocol):
    name: str
    model: str

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...
