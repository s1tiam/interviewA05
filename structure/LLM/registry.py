"""
LLM 后端注册表：按名称选择 OpenAI / Ollama / DeepSeek，统一暴露 execute(prompt) 接口。

默认后端为 **deepseek**，需在环境变量中配置：
  DEEPSEEK_API_KEY
（见 Deepseek.py）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from .Deepseek import chat_with_deepseek, DEFAULT_MAX_INPUT_CHARS as DS_MAX_IN

from .Deepseek import DEFAULT_TEMPERATURE as DS_TEMP
from .Deepseek import DEFAULT_TOP_P as DS_TOP_P
from .Ollama import DEFAULT_MAX_INPUT_CHARS as OL_MAX_IN

from .Ollama import DEFAULT_TEMPERATURE as OL_TEMP
from .Ollama import DEFAULT_TOP_P as OL_TOP_P
from .Ollama import chat_with_ollama

# OpenAI 模块无统一 DEFAULT_* 导出，在此写默认值

_OA_TEMP = 0.3
_OA_TOP = 0.95
_OA_MAX_IN = 12000


DEFAULT_MODELS: Dict[str, str] = {
    "ollama": "llama3.2",
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
}

# 未显式指定后端时使用
DEFAULT_LLM_BACKEND: str = "deepseek"

# 自定义后端：register("my_backend", callable)
_CUSTOM_BACKENDS: Dict[str, Callable[..., str]] = {}


def register(name: str, fn: Callable[..., str]) -> None:
    """注册自定义 LLM 调用函数，签名为 fn(user_prompt: str, **kwargs) -> str。"""
    key = name.strip().lower()
    if not key:
        raise ValueError("register: name 不能为空")
    _CUSTOM_BACKENDS[key] = fn


def _call_openai(model: str, system: str, user: str, **kw: Any) -> str:
    from .OpenAI import chat_with_openai

    return chat_with_openai(
        model,
        system,
        user,
        False,
        temperature=float(kw.get("temperature", _OA_TEMP)),
        top_p=float(kw.get("top_p", _OA_TOP)),
        num_completions=int(kw.get("num_completions", 1)),
        max_input_chars=int(kw.get("max_input_chars", _OA_MAX_IN)),
    )


@dataclass
class LLMClient:
    """
    与 Interviewer 兼容：提供 execute(prompt: str) -> str。
    """

    backend: str = DEFAULT_LLM_BACKEND
    model: Optional[str] = None
    system_prompt: str = "你是一名专业、简洁的中文助手。"
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.backend = self.backend.strip().lower()
        if self.model is None:
            self.model = DEFAULT_MODELS.get(self.backend, DEFAULT_MODELS[DEFAULT_LLM_BACKEND])

    def execute(self, prompt: str) -> str:
        """单轮对话：user = prompt。"""
        user = (prompt or "").strip()
        if not user:
            return ""

        if self.backend in _CUSTOM_BACKENDS:
            return _CUSTOM_BACKENDS[self.backend](user, **self.extra)

        if self.backend == "ollama":
            return chat_with_ollama(
                self.model or DEFAULT_MODELS["ollama"],
                self.system_prompt,
                user,
                False,
                temperature=float(self.extra.get("temperature", OL_TEMP)),
                top_p=float(self.extra.get("top_p", OL_TOP_P)),
                num_completions=int(self.extra.get("num_completions", 1)),
                max_input_chars=int(self.extra.get("max_input_chars", OL_MAX_IN)),
            )

        if self.backend == "openai":
            return _call_openai(
                self.model or DEFAULT_MODELS["openai"],
                self.system_prompt,
                user,
                **self.extra,
            )

        if self.backend == "deepseek":
            return chat_with_deepseek(
                user,
                systemprompt=self.system_prompt,
                model=self.model or DEFAULT_MODELS["deepseek"],
                stream=False,
                temperature=float(self.extra.get("temperature", DS_TEMP)),
                top_p=float(self.extra.get("top_p", DS_TOP_P)),
                num_completions=int(self.extra.get("num_completions", 1)),
                max_input_chars=int(self.extra.get("max_input_chars", DS_MAX_IN)),
            )

        raise ValueError(
            f"未知 LLM 后端: {self.backend!r}。可选: ollama, openai, deepseek，或先 register() 注册。"
        )


def get_llm(
    backend: str = DEFAULT_LLM_BACKEND,
    *,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    **extra: Any,
) -> LLMClient:
    """
    工厂：按名称构造 LLMClient。默认 deepseek（需 DEEPSEEK_API_KEY）。

    Examples
    --------
    >>> llm = get_llm("ollama", model="qwen2.5")
    >>> text = llm.execute("你好")
    """
    sp = system_prompt if system_prompt is not None else "你是一名专业、简洁的中文助手。"
    return LLMClient(backend=backend, model=model, system_prompt=sp, extra=dict(extra))


__all__ = [
    "LLMClient",
    "DEFAULT_MODELS",
    "DEFAULT_LLM_BACKEND",
    "get_llm",
    "register",
]
