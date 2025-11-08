"""
Coordinates extraction providers and observers.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from src.common.logging import get_logger
from src.config.settings import get_settings
from src.graph.models import Entity
from src.graph.pipeline.observers import ExtractionObserver, LoggingObserver
from src.graph.providers.base import ExtractionProviderError, ExtractionResult
from src.graph.providers.registry import ProviderRegistry


logger = get_logger("graph.pipeline.runner")


class ExtractionPipeline:
    def __init__(
        self,
        provider_registry: Optional[ProviderRegistry] = None,
        observers: Optional[Iterable[ExtractionObserver]] = None,
        allow_fallback: Optional[bool] = None,
    ):
        self.provider_registry = provider_registry or ProviderRegistry()
        self.observers: List[ExtractionObserver] = list(observers or [LoggingObserver(logger)])
        settings = get_settings()
        self.allow_fallback = (
            settings.extraction_allow_fallback if allow_fallback is None else allow_fallback
        )

    def run(self, entry: Entity, metadata: Optional[dict] = None) -> ExtractionResult:
        provider = self.provider_registry.get_extraction_provider()

        try:
            result = provider.extract(entry, metadata=metadata)
        except ExtractionProviderError as exc:
            if not self.allow_fallback:
                self._notify_failure(entry, exc)
                raise
            logger.warning("Primary provider failed: %s. Falling back to local provider.", exc)
            fallback = self.provider_registry.get_fallback_local()
            try:
                result = fallback.extract(entry, metadata=metadata)
            except Exception as fallback_exc:  # pragma: no cover - extreme failure
                self._notify_failure(entry, fallback_exc)
                raise
            else:
                self._notify_success(entry, result)
                return result
        except Exception as exc:  # pragma: no cover - guard rail
            self._notify_failure(entry, exc)
            raise
        else:
            self._notify_success(entry, result)
            return result

    def _notify_success(self, entry: Entity, result: ExtractionResult) -> None:
        for observer in self.observers:
            observer.on_success(entry, result)

    def _notify_failure(self, entry: Entity, error: Exception) -> None:
        for observer in self.observers:
            observer.on_failure(entry, error)
