"""
Service responsible for ingesting raw text entries and kicking off extraction.
"""
from __future__ import annotations

from typing import Optional

from fastapi import BackgroundTasks

from src.common.logging import get_logger
from src.config.settings import get_settings
from src.graph.models import ContentBlock, Entity, Relation, SystemLabel
from src.graph.pipeline.extraction_runner import ExtractionPipeline
from src.graph.providers.base import ExtractionResult
from src.graph.repositories.entity_repository import EntityRepository
from src.graph.repositories.relation_repository import RelationRepository
from src.graph.schemas import EntryIngestionRequest, EntryIngestionResponse
from src.graph.tasks.background import ExtractionTaskDispatcher


logger = get_logger("graph.services.entry_ingestion")


class EntryIngestionService:
    def __init__(
        self,
        entity_repository: Optional[EntityRepository] = None,
        relation_repository: Optional[RelationRepository] = None,
        pipeline: Optional[ExtractionPipeline] = None,
        dispatcher: Optional[ExtractionTaskDispatcher] = None,
    ):
        self.entity_repository = entity_repository or EntityRepository()
        self.relation_repository = relation_repository or RelationRepository()
        self.pipeline = pipeline or ExtractionPipeline()
        self.dispatcher = dispatcher or ExtractionTaskDispatcher(self.pipeline)
        settings = get_settings()
        self.require_sync = not settings.extraction_allow_fallback

    def ingest_entry(
        self,
        request: EntryIngestionRequest,
        background_tasks: Optional[BackgroundTasks] = None,
        force_sync: bool = False,
    ) -> EntryIngestionResponse:
        """ Ingest an entry into the graph. This contains the complete text of the entry """
        entry_entity = self._build_entry_entity(request)
        saved_entry = self.entity_repository.upsert(entry_entity)

        metadata = {**request.metadata, "text": request.text, "source": request.source}

        run_sync = force_sync or self.require_sync

        if run_sync:
            logger.info("Running extraction synchronously for entry %s", saved_entry.id)
            result = self.pipeline.run(saved_entry, metadata=metadata)
            self._persist_extraction(result)
            status = "processed"
        else:
            logger.info("Scheduling extraction for entry %s", saved_entry.id)
            self.dispatcher.enqueue(
                saved_entry,
                background_tasks=background_tasks,
                metadata=metadata,
                on_complete=self._persist_extraction,
            )
            status = "queued"

        return EntryIngestionResponse(entry_id=str(saved_entry.id), status=status)

    def _build_entry_entity(self, request: EntryIngestionRequest) -> Entity:
        content = ContentBlock(body=request.text, format=request.format)
        labels = list(set(request.labels or []))
        system_labels = [SystemLabel.ENTRY]

        return Entity(
            name=request.title or "Memory Entry",
            summary=request.summary,
            content=content,
            labels=labels,
            system_labels=system_labels,
            metadata=request.metadata,
        )

    def _persist_extraction(self, result: ExtractionResult) -> None:
        if not result:
            logger.warning("Extraction pipeline returned no result; skipping persistence.")
            return
        saved_entities = []
        if result.entities:
            saved_entities = self.entity_repository.bulk_create(result.entities)

        if result.relations:
            # Map relation endpoints from entity names to their persisted UUIDs when needed.
            name_to_id = {e.name: str(e.id) for e in saved_entities if e.name}

            def _resolve(endpoint: str) -> str:
                # Keep entry IDs and already-UUID-like strings; fall back to name mapping.
                return name_to_id.get(endpoint, endpoint)

            mapped_relations: list[Relation] = []
            for rel in result.relations:
                mapped_relations.append(
                    Relation(
                        source=_resolve(rel.source),
                        target=_resolve(rel.target),
                        relationType=rel.relationType,
                    )
                )
            self.relation_repository.bulk_create(mapped_relations)
