"""
Query use-cases for searching the graph.
"""
from __future__ import annotations

from src.graph.schemas import SemanticSearchRequest, TextSearchRequest
from src.graph.services.search_service import SearchService


class SearchUseCase:
    def __init__(self, service: SearchService):
        self.service = service

    def execute_text(self, request: TextSearchRequest):
        return self.service.text_search(request.query, limit=request.limit)

    def execute_semantic(self, request: SemanticSearchRequest):
        return self.service.semantic_search(request.query, limit=request.limit)
