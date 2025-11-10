"""
Ollama-backed extraction provider that prompts a local model and parses JSON output.
"""
from __future__ import annotations

import json
from textwrap import dedent
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


logger = get_logger("graph.providers.ollama")


class OllamaProvider(BaseExtractionProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        settings = get_default_provider_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_default_model
        self.timeout = timeout or settings.ollama_timeout_seconds
        self.max_retries = settings.ollama_max_retries
        self.keep_alive = settings.ollama_keep_alive
        self.context_window_tokens = settings.extraction_context_window_tokens
        self.max_chars = self.context_window_tokens * 4  # rough token->char conversion

    def extract(self, entry: Entity, metadata: Optional[dict] = None) -> ExtractionResult:
        text = self._prepare_text(entry, metadata)
        payload = {
            "model": self.model,
            "stream": False,
            "prompt": self._build_prompt(entry, text),
            "keep_alive": self.keep_alive,
            "options": {"num_ctx": min(self.context_window_tokens, 128000)},
        }

        response_json = self._perform_request(payload)
        raw = response_json.get("response", "")

        cleaned = self._clean_response(raw)
        return self._parse_response(cleaned)

    def _perform_request(self, payload: dict) -> dict:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(f"{self.base_url}/api/generate", json=payload)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException as exc:
                last_exc = exc
                logger.warning(
                    "Ollama request timed out (attempt %s/%s)", attempt, self.max_retries
                )
            except httpx.HTTPError as exc:
                last_exc = exc
                break
        raise ExtractionProviderError(f"Ollama provider request failed: {last_exc}") from last_exc

    def _prepare_text(self, entry: Entity, metadata: Optional[dict]) -> str:
        text = entry.content.body if entry.content else entry.summary or ""
        if not text and metadata:
            text = metadata.get("text", "")
        if not text and entry.metadata:
            text = entry.metadata.get("raw_text", "")
        if not text:
            raise ExtractionProviderError("ENTRY entity does not contain textual content to analyze.")
        return text if len(text) <= self.max_chars else text[: self.max_chars]

    def _build_prompt(self, entry: Entity, text: str) -> str:
        entry_id = str(entry.id)
        context_notice = (
            f"The provided text has been truncated to {self.context_window_tokens} tokens maximum."
            if len(text) >= self.max_chars
            else f"You may use up to {self.context_window_tokens} tokens."
        )
        return dedent(
            f"""
            You are Momento's knowledge graph extraction agent.
            Your job is to perform high-quality named-entity and relationship extraction
            from an unstructured journal entry and output ONLY JSON that conforms to the schema below.

            ENTRY_ID: {entry_id}
            ENTRY_LABELS: {entry.system_labels}

            {context_notice}

            RAW_ENTRY_TEXT:
            \"\"\"{text}\"\"\"

            Requirements:
            1. Identify distinct entities for people, locations, organizations, objects, events, and key concepts.
               - Ignore pronouns, stop words, months, or vague references ("he", "she", "it", "my", "december", etc.).
            2. Only the ENTRY node stores the full text; extracted entities must be concise (no long-form body).
            3. Each entity JSON object MUST include:
               - "name": short canonical name. Do NOT include an "id" field.
               - "system_labels": choose from ["PERSON","LOCATION","ORGANIZATION","OBJECT","EVENT","CONCEPT"].
               - "labels": include "extracted" plus any helpful tags (e.g. "relationship", "workplace").
               - "summary": 1-2 sentence description referencing facts from the entry.
               - "metadata": include at least {{"source_entry_id": "{entry_id}", "entity_type": "<type>"}}.
            4. Build "relations" that reflect the real relationships in the text.
               - Use uppercase snake_case relationType values like MENTIONED, WORKED_AT, MET_AT, LOCATED_IN.
               - When linking from the ENTRY to an extracted entity: set "source" to "{entry_id}" and "target" to that entity's exact "name".
               - When linking between extracted entities: set both "source" and "target" to the exact "name" strings of the entities you output.
            5. Output JSON ONLY in the form:
               {{
                 "entities": [{{...}}, {{...}}],
                 "relations": [{{...}}, {{...}}]
               }}
               No explanations, code fences, or additional text.
            """
        ).strip()

    @staticmethod
    def _clean_response(raw_response: str) -> str:
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ExtractionProviderError("Provider response did not contain JSON object.")
        return cleaned[start : end + 1]

    def _parse_response(self, raw_response: str) -> ExtractionResult:
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ExtractionProviderError("Provider response is not valid JSON") from exc

        entities_payload = parsed.get("entities", [])
        relations_payload = parsed.get("relations", [])

        if not isinstance(entities_payload, list) or not isinstance(relations_payload, list):
            raise ExtractionProviderError("Provider response missing entities/relations lists")

        entities = []
        for payload in entities_payload:
            try:
                data = Entity.model_validate(payload)
            except Exception as exc:
                logger.warning("Skipping invalid entity payload: %s", exc)
                continue
            entities.append(data)

        relations = []
        for payload in relations_payload:
            try:
                relations.append(Relation.model_validate(payload))
            except Exception as exc:
                logger.warning("Skipping invalid relation payload: %s", exc)
                continue

        if not entities and not relations:
            raise ExtractionProviderError("Provider returned empty payload")

        return ExtractionResult(entities=entities, relations=relations)
