"""
Dependency helpers for graph-related services/use-cases.
"""
from __future__ import annotations

from functools import lru_cache

from src.graph.pipeline.extraction_runner import ExtractionPipeline
from src.graph.repositories.entity_repository import EntityRepository
from src.graph.repositories.relation_repository import RelationRepository
from src.graph.services.entity_service import EntityService
from src.graph.services.entry_ingestion import EntryIngestionService
from src.graph.services.search_service import SearchService
from src.graph.tasks.background import ExtractionTaskDispatcher
from src.graph.use_cases.ingest_entry import IngestEntryUseCase
from src.graph.use_cases.semantic_search import SearchUseCase


@lru_cache
def get_entity_repository() -> EntityRepository:
    return EntityRepository()


@lru_cache
def get_relation_repository() -> RelationRepository:
    return RelationRepository()


@lru_cache
def get_extraction_pipeline() -> ExtractionPipeline:
    return ExtractionPipeline()


@lru_cache
def get_extraction_dispatcher() -> ExtractionTaskDispatcher:
    return ExtractionTaskDispatcher(get_extraction_pipeline())


@lru_cache
def get_entry_ingestion_service() -> EntryIngestionService:
    return EntryIngestionService(
        entity_repository=get_entity_repository(),
        relation_repository=get_relation_repository(),
        pipeline=get_extraction_pipeline(),
        dispatcher=get_extraction_dispatcher(),
    )


@lru_cache
def get_search_service() -> SearchService:
    return SearchService(entity_repository=get_entity_repository())


@lru_cache
def get_entity_service() -> EntityService:
    return EntityService(repository=get_entity_repository())


@lru_cache
def get_ingest_use_case() -> IngestEntryUseCase:
    return IngestEntryUseCase(service=get_entry_ingestion_service())


@lru_cache
def get_search_use_case() -> SearchUseCase:
    return SearchUseCase(service=get_search_service())
