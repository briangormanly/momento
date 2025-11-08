"""
Command use-case for ingesting a new memory entry.
"""
from __future__ import annotations

from fastapi import BackgroundTasks

from src.graph.schemas import EntryIngestionRequest, EntryIngestionResponse
from src.graph.services.entry_ingestion import EntryIngestionService


class IngestEntryUseCase:
    def __init__(self, service: EntryIngestionService):
        self.service = service

    def execute(
        self,
        request: EntryIngestionRequest,
        background_tasks: BackgroundTasks | None = None,
    ) -> EntryIngestionResponse:
        return self.service.ingest_entry(
            request,
            background_tasks=background_tasks,
            force_sync=request.process_synchronously,
        )
