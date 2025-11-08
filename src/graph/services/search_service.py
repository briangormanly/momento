"""
Search helpers (text + semantic placeholders).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from src.graph.models import Entity
from src.graph.repositories.entity_repository import EntityRepository


class SearchService:
    def __init__(self, entity_repository: Optional[EntityRepository] = None):
        self.entity_repository = entity_repository or EntityRepository()

    def text_search(self, query: str, limit: int = 20) -> List[Entity]:
        return self.entity_repository.search(query, limit=limit)

    def semantic_search(self, query: str, limit: int = 10) -> Dict[str, List[Entity]]:
        """
        Placeholder semantic search that currently delegates to text search.
        Returns a dictionary so clients can introspect which strategy was used.
        """
        results = self.entity_repository.search(query, limit=limit)
        return {
            "strategy": "text-proxy",
            "results": results,
        }
