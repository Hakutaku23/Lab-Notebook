from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMService(ABC):
    @abstractmethod
    def status(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate(self, *, task: str, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError
