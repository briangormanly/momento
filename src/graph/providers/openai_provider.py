"""
OpenAI API provider for entity extraction.
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


logger = get_logger("graph.providers.openai")


class OpenAIProvider(BaseExtractionProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
    ):
        settings = get_default_provider_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_default_model
        self.base_url = settings.openai_base_url or base_url
        self.timeout = timeout
        self._fallback = LocalLLMProvider(settings=settings)

    def extract(self, entry: Entity, metadata: Optional[dict] = None) -> ExtractionResult:
        if not self.api_key:
            logger.warning("OpenAI API key missing; falling back to local provider.")
            return self._fallback.extract(entry, metadata=metadata)

        content = self._get_source_text(entry, metadata)

        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at extracting graph entities. "
                    "Return only JSON with 'entities' and 'relations'.",
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # pragma: no cover
            logger.warning("OpenAI provider failed (%s). Falling back to local heuristic.", exc)
            return self._fallback.extract(entry, metadata=metadata)

        try:
            return self._parse_response(raw)
        except ExtractionProviderError as exc:
            logger.warning("Unable to parse OpenAI response: %s. Falling back to local provider.", exc)
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
            entry_metadata = entry.metadata or {}
            text = entry_metadata.get("raw_text", "")
        if not text and metadata:
            text = metadata.get("text", "")
        return text
