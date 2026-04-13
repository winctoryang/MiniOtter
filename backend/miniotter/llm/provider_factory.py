"""LLM provider factory."""

from __future__ import annotations

from ..config import LLMConfig
from ..exceptions import ConfigError
from .base import BaseLLMProvider
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider

_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}


class ProviderFactory:
    @staticmethod
    def create(config: LLMConfig) -> BaseLLMProvider:
        provider_cls = _PROVIDERS.get(config.provider)
        if not provider_cls:
            raise ConfigError(f"未知的 LLM 提供者: {config.provider}，支持: {', '.join(_PROVIDERS.keys())}")
        kwargs = {"api_key": config.api_key, "model": config.model}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        return provider_cls(**kwargs)

    @staticmethod
    def register(name: str, provider_cls: type[BaseLLMProvider]) -> None:
        _PROVIDERS[name] = provider_cls
