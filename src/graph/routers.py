"""
Graph ingestion/search endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.graph.dependencies import (
    get_entity_service,
    get_ingest_use_case,
    get_search_use_case,
)
from src.graph.schemas import (
    EntryIngestionRequest,
    EntryIngestionResponse,
    EntityListResponse,
    SemanticSearchRequest,
    TextSearchRequest,
)
from src.graph.services.entity_service import EntityService
from src.graph.use_cases.ingest_entry import IngestEntryUseCase
from src.graph.use_cases.semantic_search import SearchUseCase
from src.graph.providers.base import ExtractionProviderError


router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/entries", response_model=EntryIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
def ingest_entry(
    request: EntryIngestionRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    use_case: IngestEntryUseCase = Depends(get_ingest_use_case),
):
    payload = request.model_copy(deep=True)
    payload.metadata.setdefault("submitted_by", user.email)
    try:
        return use_case.execute(payload, background_tasks=background_tasks)
    except ExtractionProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Extraction provider failed: {exc}",
        ) from exc


@router.get("/entities/{entity_id}")
def get_entity(
    entity_id: str,
    user: User = Depends(get_current_user),
    service: EntityService = Depends(get_entity_service),
):
    entity = service.get(entity_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return entity


@router.get("/entities", response_model=EntityListResponse)
def list_entities(
    limit: int = 50,
    skip: int = 0,
    user: User = Depends(get_current_user),
    service: EntityService = Depends(get_entity_service),
):
    items = service.list(limit=limit, skip=skip)
    return EntityListResponse(items=items, total=len(items))


@router.post("/search/text")
def text_search(
    request: TextSearchRequest,
    user: User = Depends(get_current_user),
    use_case: SearchUseCase = Depends(get_search_use_case),
):
    return use_case.execute_text(request)


@router.post("/search/semantic")
def semantic_search(
    request: SemanticSearchRequest,
    user: User = Depends(get_current_user),
    use_case: SearchUseCase = Depends(get_search_use_case),
):
    return use_case.execute_semantic(request)
