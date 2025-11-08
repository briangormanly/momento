"""
High-level operations for working with Entity nodes.
"""
from __future__ import annotations

from typing import List, Optional

from src.graph.models import Entity
from src.graph.repositories.entity_repository import EntityRepository


class EntityService:
    def __init__(self, repository: Optional[EntityRepository] = None):
        self.repository = repository or EntityRepository()

    def get(self, entity_id: str) -> Optional[Entity]:
        return self.repository.get(entity_id)

    def list(self, limit: int = 50, skip: int = 0) -> List[Entity]:
        return self.repository.list(limit=limit, skip=skip)

    def search(self, query_text: str, limit: int = 20) -> List[Entity]:
        return self.repository.search(query_text, limit=limit)

    def delete(self, entity_id: str) -> bool:
        return self.repository.delete(entity_id)
