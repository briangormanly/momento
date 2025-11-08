"""
Provider registry/factory for extraction engines.
"""
from __future__ import annotations

from typing import Dict

from src.common.logging import get_logger
from src.config.settings import get_settings
from src.graph.providers.anthropic_provider import AnthropicProvider
from src.graph.providers.base import BaseExtractionProvider
from src.graph.providers.local_provider import LocalLLMProvider
from src.graph.providers.ollama_provider import OllamaProvider
from src.graph.providers.openai_provider import OpenAIProvider


logger = get_logger("graph.providers.registry")


class ProviderRegistry:
    def __init__(self):
        self.settings = get_settings()
        self._instances: Dict[str, BaseExtractionProvider] = {}

    def get_extraction_provider(self) -> BaseExtractionProvider:
        key = (self.settings.extraction_provider or "local").lower()
        if key not in self._instances:
            self._instances[key] = self._build_provider(key)
        return self._instances[key]

    def _build_provider(self, key: str) -> BaseExtractionProvider:
        if key == "ollama":
            return OllamaProvider()
        if key == "openai":
            return OpenAIProvider()
        if key == "anthropic":
            return AnthropicProvider()

        if key != "local":
            logger.warning("Unknown provider '%s'; defaulting to local heuristic.", key)
        return LocalLLMProvider()

    def get_fallback_local(self) -> BaseExtractionProvider:
        if "local" not in self._instances:
            self._instances["local"] = LocalLLMProvider()
        return self._instances["local"]
