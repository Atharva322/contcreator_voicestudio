import logging
import time
from collections.abc import Callable
from typing import Any

from app.config import get_settings
from app.services.providers import JsonGenerationProvider, OpenAIProvider, ProviderFailure, ProviderFailureCategory

logger = logging.getLogger(__name__)

ResultValidator = Callable[[dict[str, Any]], dict[str, Any]]


class AIClient:
    def __init__(self, provider: JsonGenerationProvider | None = None) -> None:
        self.settings = get_settings()
        self.provider = provider
        if self.provider is None and self.settings.openai_api_key:
            self.provider = OpenAIProvider(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                timeout_seconds=self.settings.openai_timeout_seconds,
            )

    def json_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any],
        *,
        operation: str = "json_completion",
        validator: ResultValidator | None = None,
    ) -> dict[str, Any]:
        if not self.provider:
            self._log_result(operation, "heuristic", None, 0, True, "no_api_key")
            return fallback

        started = time.perf_counter()
        try:
            result = self.provider.generate_json(system_prompt, user_prompt)
            if validator:
                result = validator(result)
        except ProviderFailure as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            self._log_result(operation, self.provider.name, self.provider.model, duration_ms, True, exc.category.value)
            return fallback

        duration_ms = int((time.perf_counter() - started) * 1000)
        self._log_result(operation, self.provider.name, self.provider.model, duration_ms, False, None)
        return result

    def _log_result(
        self,
        operation: str,
        provider: str,
        model: str | None,
        duration_ms: int,
        fallback: bool,
        category: str | None,
    ) -> None:
        logger.info(
            "ai_generation_result operation=%s provider=%s model=%s duration_ms=%s fallback=%s failure_category=%s",
            operation,
            provider,
            model,
            duration_ms,
            fallback,
            category,
        )


def invalid_shape(message: str) -> ProviderFailure:
    return ProviderFailure(ProviderFailureCategory.invalid_shape, message)
