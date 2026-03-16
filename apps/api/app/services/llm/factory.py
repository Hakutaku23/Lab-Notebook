from __future__ import annotations

from app.core.config import settings
from app.services.llm.base import LLMService
from app.services.llm.providers import MockLLMService, NoneLLMService


def get_llm_service() -> LLMService:
    provider = settings.llm_provider.lower().strip()
    if provider == "mock":
        return MockLLMService()
    return NoneLLMService()
