from __future__ import annotations

import json

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError

from app.services.providers.types import ProviderFailure, ProviderFailureCategory


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, timeout_seconds: float) -> None:
        self.model = model
        self.client = OpenAI(api_key=api_key, timeout=timeout_seconds)
        self.timeout_seconds = timeout_seconds

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.35,
                timeout=self.timeout_seconds,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except APITimeoutError as exc:
            raise ProviderFailure(ProviderFailureCategory.timeout, "OpenAI request timed out") from exc
        except APIConnectionError as exc:
            raise ProviderFailure(ProviderFailureCategory.connection, "OpenAI connection failed") from exc
        except RateLimitError as exc:
            raise ProviderFailure(ProviderFailureCategory.rate_limit, "OpenAI rate limit exceeded") from exc
        except InternalServerError as exc:
            raise ProviderFailure(ProviderFailureCategory.provider_temporary, "OpenAI temporary server failure") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise ProviderFailure(ProviderFailureCategory.empty_response, "OpenAI returned empty content")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderFailure(ProviderFailureCategory.invalid_json, "OpenAI returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise ProviderFailure(ProviderFailureCategory.invalid_json, "OpenAI returned non-object JSON")
        return parsed
