from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel, Field


class LLMRuntimeConfigIn(BaseModel):
    mode: Literal["local", "api_key"] = "local"
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None


class LLMStatusOut(BaseModel):
    provider: str
    mode: Literal["local", "api_key", "mock", "none"] = "local"
    model: str | None = None
    enabled: bool
    configured: bool = False
    supports_generation: bool
    message: str
    base_url: str | None = None


class LLMStatusCheckIn(BaseModel):
    config: LLMRuntimeConfigIn


class LLMGenerateIn(BaseModel):
    task: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1)
    context: dict[str, Any] | None = None
    config: LLMRuntimeConfigIn | None = None


class LLMGenerateOut(BaseModel):
    provider: str
    mode: Literal["local", "api_key", "mock", "none"] = "local"
    model: str | None = None
    content: str
    raw: dict[str, Any] | None = None
