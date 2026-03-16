from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LLMStatusOut(BaseModel):
    provider: str
    model: str | None = None
    enabled: bool
    supports_generation: bool
    message: str


class LLMGenerateIn(BaseModel):
    task: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1)
    context: dict[str, Any] | None = None


class LLMGenerateOut(BaseModel):
    provider: str
    model: str | None = None
    content: str
    raw: dict[str, Any] | None = None
