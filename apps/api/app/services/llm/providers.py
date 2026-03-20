from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from fastapi import HTTPException, status

from app.core.config import settings
from app.services.llm.base import LLMService


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@dataclass(slots=True)
class LLMRuntimeConfig:
    mode: str = "local"
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None) -> "LLMRuntimeConfig":
        payload = data or {}
        mode = _clean_string(payload.get("mode")) or "local"
        return cls(
            mode=mode.lower(),
            base_url=_clean_string(payload.get("base_url")),
            model=_clean_string(payload.get("model")),
            api_key=_clean_string(payload.get("api_key")),
        )


def _build_chat_completion_url(base_url: str | None) -> str | None:
    if not base_url:
        return None

    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/chat/completions"
    return f"{normalized}/v1/chat/completions"


def _build_user_prompt(prompt: str, context: dict[str, Any] | None = None) -> str:
    parts = [prompt.strip()]
    if context:
        parts.append("")
        parts.append("补充上下文如下，请在回答时一并参考：")
        parts.append(json.dumps(context, ensure_ascii=False, indent=2))
    return "\n".join(parts).strip()


def _extract_message_content(raw: dict[str, Any]) -> str:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="模型服务返回结果缺少 choices，无法解析。",
        )

    message = choices[0].get("message", {})
    content = message.get("content")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text.strip())
        if text_parts:
            return "\n".join(text_parts)

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="模型服务返回内容为空，无法生成结果。",
    )


class NoneLLMService(LLMService):
    def status(self) -> dict[str, Any]:
        return {
            "provider": "none",
            "mode": "none",
            "model": None,
            "enabled": False,
            "configured": False,
            "supports_generation": False,
            "base_url": None,
            "message": "当前未启用任何模型服务，AI 能力仅保留接口占位。",
        }

    def generate(self, *, task: str, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="当前没有可用的模型服务，请先配置本地模型或 API key。",
        )


class MockLLMService(LLMService):
    def status(self) -> dict[str, Any]:
        return {
            "provider": "mock",
            "mode": "mock",
            "model": settings.llm_model or "mock-summary-model",
            "enabled": True,
            "configured": True,
            "supports_generation": True,
            "base_url": None,
            "message": "当前使用 mock provider，便于前后端联调 AI 交互流程。",
        }

    def generate(self, *, task: str, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context_lines: list[str] = []
        if context:
            for key, value in context.items():
                context_lines.append(f"- {key}: {value}")
        content = "\n".join(
            [
                f"[mock:{task}]",
                "以下内容为联调占位输出，不代表真实模型结果。",
                prompt.strip(),
                *context_lines,
            ]
        )
        return {
            "provider": "mock",
            "mode": "mock",
            "model": settings.llm_model or "mock-summary-model",
            "content": content,
            "raw": {"task": task, "context": context or {}},
        }


class OpenAICompatibleLLMService(LLMService):
    def __init__(self, runtime: LLMRuntimeConfig, *, provider: str) -> None:
        self.runtime = runtime
        self.provider = provider

    def _status_message(self) -> tuple[bool, str]:
        if not self.runtime.base_url or not self.runtime.model:
            if self.runtime.mode == "api_key":
                return False, "请先在 AI 设置中填写模型服务地址、模型名称和 API key。"
            return False, "当前默认使用本地模型，但尚未配置本地模型服务地址和模型名称。"

        if self.runtime.mode == "api_key" and not self.runtime.api_key:
            return False, "已切换为 API key 模式，但还没有填写 API key。"

        if self.runtime.mode == "api_key":
            return True, "API key 模式已配置完成，调用时将优先使用你填写的模型服务。"
        return True, "本地模型配置已就绪，请确认本机或局域网中的模型服务正在运行。"

    def status(self) -> dict[str, Any]:
        configured, message = self._status_message()
        return {
            "provider": self.provider,
            "mode": self.runtime.mode,
            "model": self.runtime.model,
            "enabled": configured,
            "configured": configured,
            "supports_generation": configured,
            "base_url": self.runtime.base_url,
            "message": message,
        }

    def _build_system_prompt(self, task: str) -> str:
        task_name = task.strip().lower()
        if task_name == "template_json":
            return (
                "你是实验记录系统的模板设计助手。"
                "请根据用户需求直接输出合法 JSON，顶层必须是 sections 数组，不要添加 Markdown 代码块。"
                "每个 section 需要包含 key、title、description、order_index、is_repeatable、fields。"
                "每个 field 需要包含 key、label、field_type、required、order_index，"
                "并按需补充 placeholder、help_text、default_value、options、validation_rules、ui_props。"
            )
        if task_name == "record_summary":
            return "你是实验记录系统的科研写作助手，请用中文生成简洁、准确、可直接粘贴到记录摘要中的实验总结。"
        if task_name == "record_polish":
            return "你是实验记录系统的科研写作助手，请用中文润色用户已有摘要，保持事实不变、表达更清晰专业。"
        if task_name == "record_field":
            return (
                "你是实验记录系统的字段填写助手。"
                "请围绕目标字段输出可直接回填的内容，优先参考字段标签、帮助文本、当前摘要、同页其它字段和实验上下文。"
                "如果字段是 JSON、table 或 file，请直接输出合法 JSON，不要添加 Markdown 代码块。"
            )
        if task_name == "record_quality":
            return (
                "你是实验记录系统的记录质检助手。"
                "请从完整性、风险点、一致性和审核可读性角度进行检查，输出中文结论，并尽量使用条目化建议。"
            )
        return "你是实验记录系统内置的 AI 助手，请用中文提供清晰、直接、可执行的回答。"

    def _send_chat_completion(self, task: str, prompt: str, context: dict[str, Any] | None) -> dict[str, Any]:
        status_payload = self.status()
        if not status_payload["configured"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=status_payload["message"],
            )

        url = _build_chat_completion_url(self.runtime.base_url)
        if not url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="模型服务地址缺失，无法发起请求。",
            )

        payload = {
            "model": self.runtime.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": self._build_system_prompt(task)},
                {"role": "user", "content": _build_user_prompt(prompt, context)},
            ],
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.runtime.api_key:
            headers["Authorization"] = f"Bearer {self.runtime.api_key}"

        request = urllib_request.Request(url=url, data=data, headers=headers, method="POST")

        try:
            with urllib_request.urlopen(request, timeout=settings.llm_timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore").strip()
            message = detail or exc.reason or "模型服务返回了错误响应。"
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"模型调用失败：{message[:500]}",
            ) from exc
        except urllib_error.URLError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="无法连接到模型服务，请检查本地模型进程、服务地址或网络访问配置。",
            ) from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="模型服务返回了无法解析的内容。",
            ) from exc

    def generate(self, *, task: str, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raw = self._send_chat_completion(task, prompt, context)
        return {
            "provider": self.provider,
            "mode": self.runtime.mode,
            "model": self.runtime.model,
            "content": _extract_message_content(raw),
            "raw": raw,
        }


class LocalLLMService(OpenAICompatibleLLMService):
    def __init__(self, runtime: LLMRuntimeConfig) -> None:
        super().__init__(runtime, provider="local")


class APIKeyLLMService(OpenAICompatibleLLMService):
    def __init__(self, runtime: LLMRuntimeConfig) -> None:
        super().__init__(runtime, provider="api_key")
