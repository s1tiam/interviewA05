"""LLM 子包：统一注册表与多后端对话。"""

from .registry import DEFAULT_LLM_BACKEND, DEFAULT_MODELS, LLMClient, get_llm, register

__all__ = ["DEFAULT_LLM_BACKEND", "DEFAULT_MODELS", "LLMClient", "get_llm", "register"]
