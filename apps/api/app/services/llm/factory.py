from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.llm.base import LLMService
from app.services.llm.providers import (
    APIKeyLLMService,
    LLMRuntimeConfig,
    LocalLLMService,
    MockLLMService,
    NoneLLMService,
)


def _runtime_from_settings() -> LLMRuntimeConfig:
    provider = settings.llm_provider.lower().strip() or "local"
    if provider == "none":
        return LLMRuntimeConfig(mode="none")
    if provider == "mock":
        return LLMRuntimeConfig(mode="mock", model=settings.llm_model or "mock-summary-model")
    return LLMRuntimeConfig(
        mode="local",
        base_url=settings.llm_base_url or None,
        model=settings.llm_model or None,
        api_key=settings.llm_api_key or None,
    )


def get_llm_service(config: dict[str, Any] | None = None) -> LLMService:
    runtime = LLMRuntimeConfig.from_mapping(config) if config else _runtime_from_settings()
    provider = runtime.mode.lower().strip()

    if provider == "mock":
        return MockLLMService()
    if provider == "api_key":
        return APIKeyLLMService(runtime)
    if provider == "none":
        return NoneLLMService()
    return LocalLLMService(runtime)
