"""
Anthropic Claude provider for entity extraction.
"""
from __future__ import annotations

import json
from typing import Optional

import httpx

from src.common.logging import get_logger
from src.graph.models import Entity, Relation
from src.graph.providers.base import (
    BaseExtractionProvider,
    ExtractionProviderError,
    ExtractionResult,
    get_default_provider_settings,
)
from src.graph.providers.local_provider import LocalLLMProvider


logger = get_logger("graph.providers.anthropic")


class AnthropicProvider(BaseExtractionProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        settings = get_default_provider_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.anthropic_default_model
        self.timeout = timeout
        self._fallback = LocalLLMProvider(settings=settings)

    def extract(self, entry: Entity, metadata: Optional[dict] = None) -> ExtractionResult:
        if not self.api_key:
            logger.warning("Anthropic API key missing; falling back to local provider.")
            return self._fallback.extract(entry, metadata=metadata)

        content = self._get_source_text(entry, metadata)

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
            "system": (
                "You are part of the Momento memory graph. "
                "Return JSON with 'entities' and 'relations' following the provided schema."
            ),
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
                response.raise_for_status()
                content = response.json()["content"][0]["text"]
        except Exception as exc:  # pragma: no cover
            logger.warning("Anthropic provider failed (%s). Falling back to local heuristic.", exc)
            return self._fallback.extract(entry, metadata=metadata)

        try:
            return self._parse_response(content)
        except ExtractionProviderError as exc:
            logger.warning("Unable to parse Anthropic response: %s. Falling back to local provider.", exc)
            return self._fallback.extract(entry, metadata=metadata)

    def _parse_response(self, raw_response: str) -> ExtractionResult:
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ExtractionProviderError("Provider response is not valid JSON") from exc

        entities = [Entity.model_validate(obj) for obj in parsed.get("entities", []) if isinstance(obj, dict)]
        relations = [Relation.model_validate(obj) for obj in parsed.get("relations", []) if isinstance(obj, dict)]

        if not entities and not relations:
            raise ExtractionProviderError("Provider returned empty payload")

        return ExtractionResult(entities=entities, relations=relations)

    @staticmethod
    def _get_source_text(entry: Entity, metadata: Optional[dict]) -> str:
        text = entry.content.body if entry.content else entry.summary or ""
        if not text:
            text = entry.metadata.get("raw_text", "")
        if not text and metadata:
            text = metadata.get("text", "")
        return text
