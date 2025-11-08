"""
Observer hooks that react to pipeline events (metrics, logging, etc.).
"""
from __future__ import annotations

from typing import Protocol

from src.graph.models import Entity
from src.graph.providers.base import ExtractionResult


class ExtractionObserver(Protocol):
    """Protocol for reacting to extraction lifecycle events."""

    def on_success(self, entry: Entity, result: ExtractionResult) -> None: ...

    def on_failure(self, entry: Entity, error: Exception) -> None: ...


class LoggingObserver:
    """Default observer that logs pipeline progress."""

    def __init__(self, logger):
        self.logger = logger

    def on_success(self, entry: Entity, result: ExtractionResult) -> None:  # pragma: no cover - thin logging
        self.logger.info(
            "Extraction completed for entry=%s entities=%s relations=%s",
            entry.id,
            len(result.entities),
            len(result.relations),
        )

    def on_failure(self, entry: Entity, error: Exception) -> None:  # pragma: no cover
        self.logger.exception("Extraction failed for entry=%s: %s", entry.id, error)
