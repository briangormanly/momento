"""
Helpers for dispatching long running graph-processing tasks.
"""
from __future__ import annotations

from typing import Callable, Optional

from fastapi import BackgroundTasks

from src.common.logging import get_logger
from src.graph.models import Entity
from src.graph.pipeline.extraction_runner import ExtractionPipeline
from src.graph.providers.base import ExtractionResult


logger = get_logger("graph.tasks")


class ExtractionTaskDispatcher:
    """
    Thin wrapper that allows FastAPI BackgroundTasks to run the extraction pipeline.
    """

    def __init__(self, pipeline: ExtractionPipeline):
        self.pipeline = pipeline

    def enqueue(
        self,
        entry_entity: Entity,
        background_tasks: Optional[BackgroundTasks] = None,
        metadata: Optional[dict] = None,
        on_complete: Optional[Callable[[ExtractionResult], None]] = None,
    ) -> None:
        """
        Schedule the extraction pipeline to run asynchronously. Falls back to synchronous
        execution if BackgroundTasks is not available (e.g. CLI ingestion).
        """
        if background_tasks:
            background_tasks.add_task(self._run_pipeline_safe, entry_entity, metadata, on_complete)
            return

        self._run_pipeline_safe(entry_entity, metadata, on_complete)

    def _run_pipeline_safe(
        self,
        entry_entity: Entity,
        metadata: Optional[dict],
        on_complete: Optional[Callable[[ExtractionResult], None]],
    ) -> None:
        try:
            result = self.pipeline.run(entry_entity, metadata=metadata or {})
            if on_complete:
                on_complete(result)
        except Exception as exc:  # pragma: no cover - guard rail
            logger.exception("Extraction pipeline failed for %s: %s", entry_entity.id, exc)
