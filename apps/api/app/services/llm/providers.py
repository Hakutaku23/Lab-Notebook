from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.services.llm.base import LLMService


class NoneLLMService(LLMService):
    def status(self) -> dict[str, Any]:
        return {
            "provider": "none",
            "model": None,
            "enabled": False,
            "supports_generation": False,
            "message": "未配置 LLM Provider，当前仅保留统一接口层。",
        }

    def generate(self, *, task: str, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="当前未配置可用的 LLM Provider。",
        )


class MockLLMService(LLMService):
    def status(self) -> dict[str, Any]:
        return {
            "provider": "mock",
            "model": settings.llm_model or "mock-summary-model",
            "enabled": True,
            "supports_generation": True,
            "message": "当前使用 mock provider，便于前后端先联调统一接口。",
        }

    def generate(self, *, task: str, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context_lines: list[str] = []
        if context:
            for key, value in context.items():
                context_lines.append(f"- {key}: {value}")
        content = "\n".join(
            [
                f"[mock:{task}]",
                "以下内容为接口联调占位输出，不代表真实大模型结果。",
                prompt.strip(),
                *context_lines,
            ]
        )
        return {
            "provider": "mock",
            "model": settings.llm_model or "mock-summary-model",
            "content": content,
            "raw": {"task": task, "context": context or {}},
        }
