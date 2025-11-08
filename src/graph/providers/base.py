"""
Base provider interfaces for running extraction/embedding workloads.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol

from src.config.settings import get_settings
from src.graph.models import Entity, Relation


class ExtractionProviderError(RuntimeError):
    """Raised when an extraction provider cannot return a result."""


@dataclass
class ExtractionResult:
    entities: List[Entity] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)


class BaseExtractionProvider(Protocol):
    """
    Protocol for providers that can transform an ENTRY entity into additional graph nodes.
    """

    def extract(self, entry: Entity, metadata: Optional[dict] = None) -> ExtractionResult: ...


def get_default_provider_settings():
    """
    Helper for classes that need lazily loaded settings without circular imports.
    """
    return get_settings()
