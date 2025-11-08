"""
Heuristic provider used for local development/testing without an external LLM.
"""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional
from uuid import uuid4

from src.common.logging import get_logger
from src.graph.models import Entity, Observation, Relation, SystemLabel
from src.graph.providers.base import BaseExtractionProvider, ExtractionResult, get_default_provider_settings


logger = get_logger("graph.providers.local")

PERSON_HINTS = {"Brian", "Yoli", "Eric", "Darren"}
LOCATION_HINTS = {"Hopewell Junction", "Poughkeepsie"}
ORGANIZATION_HINTS = {"Twilight Florist"}
EVENT_HINTS = {"date", "meeting", "first date"}
STOPWORDS = {
    "he",
    "she",
    "it",
    "we",
    "i",
    "my",
    "me",
    "you",
    "they",
    "december",
    "october",
    "mid",
    "first",
}


class LocalLLMProvider(BaseExtractionProvider):
    """
    Rudimentary extractor that derives entities/relations from capitalized tokens.
    Serves as a deterministic stand-in for real LLM providers.
    """

    def __init__(self, settings=None):
        self.settings = settings or get_default_provider_settings()

    def extract(self, entry: Entity, metadata: Optional[dict] = None) -> ExtractionResult:
        text = entry.content.body if entry.content else entry.summary or ""
        if not text and metadata:
            text = metadata.get("text", "")
        if not text:
            logger.info("Local provider received entry without content; returning no-op result.")
            return ExtractionResult()

        names = self._extract_named_entities(text)
        entities = [self._build_entity(name, entry) for name in names]
        relations = [self._build_relation(entry, entity) for entity in entities]

        return ExtractionResult(entities=entities, relations=relations)

    def _extract_named_entities(self, text: str) -> List[str]:
        """
        Simple name extractor that looks for capitalized words/pairs.
        """
        candidates = set()
        pattern = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b")
        for match in pattern.findall(text):
            normalized = match.strip()
            if normalized.lower() in STOPWORDS:
                continue
            candidates.add(normalized)

        candidates.update(name for name in PERSON_HINTS if name in text)
        return sorted(candidates)

    def _build_entity(self, name: str, entry: Entity) -> Entity:
        system_label = self._infer_system_label(name)
        labels = ["generated", "extracted"]
        if system_label == SystemLabel.LOCATION:
            labels.append("location")
        elif system_label == SystemLabel.ORGANIZATION:
            labels.append("organization")

        observations = [
            Observation(
                text=f"Mentioned alongside entry {entry.id}",
                metadata={"source_entry_id": str(entry.id)},
            )
        ]
        return Entity(
            name=name,
            system_labels=[system_label],
            labels=labels,
            observations=observations,
            metadata={"generated_by": "local-provider", "entity_type": system_label.value},
        )

    def _infer_system_label(self, name: str) -> SystemLabel:
        if name in LOCATION_HINTS or name.lower().endswith(("junction", "poughkeepsie")):
            return SystemLabel.LOCATION
        if name in ORGANIZATION_HINTS or "Florist" in name:
            return SystemLabel.ORGANIZATION
        if name in EVENT_HINTS or "date" in name.lower():
            return SystemLabel.EVENT
        return SystemLabel.PERSON

    def _build_relation(self, entry: Entity, entity: Entity) -> Relation:
        return Relation(
            source=str(entry.id),
            target=str(entity.id),
            relationType="MENTIONS",
        )
